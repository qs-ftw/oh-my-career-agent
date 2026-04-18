# Check-Work MCP Server + Skill 设计文档

> 日期：2026-04-17
> 状态：待审批

## 概述

开发一个 MCP Server + Skill 组合，让用户在 Claude Code 中完成代码开发后，通过 `/check-work` 命令将代码成果转化为 Achievement 并发布到 CareerAgent 平台。

核心价值：利用 Claude 在编码环境中独有的代码仓库访问能力和对话上下文，提供比平台端更深度的成果分析。

## 架构

```
┌─────────────────────────────────────────────────┐
│  Claude Code                                     │
│                                                  │
│  /check-work (Skill)                             │
│  ┌─────────────────────────────────────────┐     │
│  │ 1. 上下文收集 (git + 对话)               │     │
│  │ 2. 成果初稿生成                          │     │
│  │ 3. 交互式编辑                            │     │
│  │ 4. 本地深度分析 (四维度)                  │     │
│  │ 5. 确认发布 ──────┐                      │     │
│  └────────────────────┼────────────────────┘     │
│                       ▼                          │
│  MCP Server (CareerAgent API Client)             │
│  ┌─────────────────────────────────────────┐     │
│  │ career_create_achievement                │     │
│  │ career_list_achievements                 │     │
│  │ career_update_achievement                │     │
│  │ career_create_project                    │     │
│  │ career_list_projects                     │     │
│  │ career_list_roles                        │     │
│  │ career_list_work_experiences             │     │
│  └──────────────────┬──────────────────────┘     │
│                     ▼                            │
│            CareerAgent FastAPI                    │
│            (localhost:8000)                       │
└─────────────────────────────────────────────────┘
```

**职责划分**：
- **MCP Server**：纯数据通道，封装 CareerAgent REST API 为 MCP 工具
- **Skill**：交互编排 + 本地分析，利用 Claude 原生能力（git、代码理解、多轮对话）

## MCP Server 设计

### 技术栈

- Python 3.11+
- `mcp` 包（FastMCP）
- `httpx` 异步 HTTP 客户端

### 文件结构

```
mcp/careeragent-mcp/
├── pyproject.toml       # 依赖声明
├── README.md
└── src/
    └── careeragent_mcp/
        ├── __init__.py
        └── server.py    # MCP Server 主文件
```

### 工具列表

| 工具名 | HTTP 方法 | API 路径 | 参数 |
|--------|-----------|----------|------|
| `career_create_achievement` | POST | `/api/achievements` | title, raw_content, tags, project_id, source_type, date_occurred |
| `career_list_achievements` | GET | `/api/achievements` | status, project_id（可选筛选） |
| `career_get_achievement` | GET | `/api/achievements/{id}` | id |
| `career_update_achievement` | PATCH | `/api/achievements/{id}` | id, 以及可更新字段 |
| `career_create_project` | POST | `/api/projects` | name, description, tech_stack, url, start_date, end_date |
| `career_list_projects` | GET | `/api/projects` | 无 |
| `career_list_roles` | GET | `/api/roles` | 无 |
| `career_list_work_experiences` | GET | `/api/work-experiences` | 无 |

### 配置

- 环境变量 `CAREERAGENT_API_URL`，默认 `http://localhost:8000`
- 注册命令：`claude mcp add careeragent -- python mcp/careeragent-mcp/src/careeragent_mcp/server.py`

## Skill `/check-work` 设计

### 触发条件

用户在 Claude Code 中输入 `/check-work`。

### 执行流程

#### Step 1：上下文收集

**有新 commits 的情况**：
1. 运行 `git log --oneline` 获取最近一次会话产生的 commits（基于时间或 HEAD 变化）
2. 运行 `git diff` 获取变更详情（stat + 具体改动）
3. Claude 回顾当前对话历史，提取关键上下文（需求背景、技术决策、解决思路）

**无新 commits 的情况**：
1. 告知用户当前没有新的代码提交
2. 询问用户意图，提供选项：
   - 选择项目中的某个模块/功能，整理其开发历程为成果
   - 回顾最近的工作经历，手动描述成果
   - 查看最近的 commits 历史，选择一个时间范围来整理
3. 根据用户选择进入对应的收集模式

#### Step 2：成果初稿生成

Claude 基于收集的上下文自动生成：

```json
{
  "title": "一句话概括这次工作",
  "raw_content": "STAR 格式的详细描述",
  "tags": ["自动", "提取的", "技术标签"],
  "tech_stack": ["涉及的技术栈"],
  "source_type": "code_session"
}
```

生成规则：
- `title`：简洁明了，突出核心价值（如 "实现教育模块的级联删除与 Markdown 导出"）
- `raw_content`：遵循 STAR 方法（Situation-Task-Action-Result），融入对话中提取的决策背景
- `tags`：从代码 diff 和对话中提取技术关键词
- `source_type`：固定为 `code_session`，区分手动创建的成果

#### Step 3：交互式编辑

在终端中逐字段展示初稿，询问用户：

1. 展示完整初稿
2. 询问是否满意，或希望修改哪些字段
3. 如果用户选择修改，逐字段引导编辑
4. 用户可以在任何环节补充额外信息（Claude 会将这些信息融入分析）

交互风格参考 CareerAgent 平台的交互式分析（温暖鼓励型教练风格），但适配终端场景——更简洁、更高效。

#### Step 4：本地深度分析

四个分析维度，全部由 Claude 本地完成，不调用 CareerAgent 后端分析接口：

**技术维度分析**：
- 从代码 diff 中识别技术栈和架构模式
- 提取核心技术决策及其原因（结合对话上下文）
- 识别解决的复杂技术问题和采用的方案
- 产出：technical_points、challenges、solutions

**能力维度分析**：
- 从对话和代码中识别体现的软技能
- 包括：问题分析与定位能力、技术方案设计能力、协作沟通、技术领导力等
- 产出：capability_tags、interview_points

**项目关联**：
- 通过 MCP 查询已有项目列表
- 基于代码变更路径和技术栈匹配最相关的项目
- 如果没有匹配的项目，建议创建新项目（自动填充 name、description、tech_stack）
- 产出：project_id 或新建项目建议

**角色匹配**：
- 通过 MCP 查询用户的目标角色列表
- 分析成果内容与各角色的匹配度（类似后端 role_matching 节点的逻辑）
- 只推荐 match_score >= 0.3 的角色
- 产出：角色匹配列表，附带匹配原因

#### Step 5：确认发布

1. 展示最终成果卡片（结构化展示所有字段和分析结果）
2. 用户确认后：
   - 如果需要新建项目 → 通过 MCP `career_create_project` 创建
   - 通过 MCP `career_create_achievement` 发布成果（包含所有分析结果作为 parsed_data）
   - 如果有关联的角色匹配信息，一并写入
3. 返回发布成功的确认信息（包含 Achievement ID）

### Prompt 设计

深度分析复用 CareerAgent 后端的 prompt 结构，但增加代码上下文维度：

- **技术分析 prompt**：参考 `backend/src/agent/nodes/achievement_analysis.py` 的 `_SYSTEM_PROMPT`，增加"你拥有完整的代码变更信息和对话上下文"的指导
- **角色匹配 prompt**：参考 `backend/src/agent/nodes/role_matching.py` 的 `_SYSTEM_PROMPT`
- **交互式引导**：参考 `backend/src/services/interactive_analysis_service.py` 的 `_SYSTEM_PROMPT`，但适配终端交互场景

### 错误处理

| 场景 | 处理方式 |
|------|----------|
| MCP Server 未启动 | 提示用户 CareerAgent MCP 服务未连接，指导启动 |
| CareerAgent 后端不可达 | 提示用户 CareerAgent 后端未运行，指导启动 |
| 无 git 仓库 | 提示当前目录不是 git 仓库 |
| 无新 commits | 进入引导模式，让用户选择要整理的成果来源 |
| API 认证失败 | 提示认证配置问题 |

## 与 CareerAgent 现有系统的关系

- **不替代**：平台端的 Achievement 分析和交互式分析仍然保留，给不使用编码智能体的用户
- **增强**：`/check-work` 提供了更深度的分析（因为能访问代码仓库和完整对话上下文）
- **数据兼容**：通过 API 创建的 Achievement 与平台端手动创建的完全一致，平台端可以继续后续处理
- **source_type 区分**：使用 `code_session` 标识来源，方便后续筛选和统计

## 开发范围

### 包含

1. MCP Server（Python，约 8 个工具）
2. Skill 文件（SKILL.md）
3. MCP 注册配置
4. 基础错误处理

### 不包含

- 平台端前端改动
- 后端 API 新增或修改
- 用户认证系统
- 成果模板系统
