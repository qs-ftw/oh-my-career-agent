<div align="center">

# oh-my-career-agent

**AI 驱动的软件工程师职业资产管理系统**

不是一次性简历工具，而是一套持续运行的系统——把你的真实工作成果转化为
岗位定制简历、能力 Gap 分析和 JD 定制方案。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev/)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/qs-ftw/oh-my-career-agent/pulls)

**中文** | [English](./README.md)

</div>

---

## 为什么需要 oh-my-career-agent？

你同时准备多个求职方向。你每天积累工作成果。你需要针对每份 JD 定制简历。但传统工具把这些当孤立任务处理。

oh-my-career-agent 把它们串起来：

- **长期记忆** — 为每个目标岗位维护独立档案，资产持续积累
- **真实成果驱动** — 每条简历内容都追溯到真实工作，拒绝虚构
- **Agent 驱动，而非模板驱动** — 7 个专业 AI Agent 分析、匹配、评分、解释
- **代码直接变成果** — 在 IDE 里完成开发后，一键转化为职业资产

## 功能特性

### 多岗位目标管理

同时维护多个求职方向的独立简历（后端工程师、AI 工程师、全栈等）。每个岗位拥有独立的能力模型、主简历版本和 Gap 列表。

### 成果沉淀流水线

提交工作成果，AI Agent 流水线自动分析、匹配目标岗位、生成简历更新建议。资产持续积累，不再遗忘。

### 代码转成果（`/check-work`）

开发者的杀手级功能。在 Claude Code 中完成编码后运行 `/check-work`，自动捕获 git 变更和对话上下文，生成成果初稿，经过四维度深度分析（技术分析、能力分析、项目关联、角色匹配），直接发布到 CareerAgent 平台。

### Gap 分析

结构化展示每个目标岗位的能力差距：缺少什么技能、什么技能有但缺证据、什么需要更深入的项目经验。新成果录入后自动重新评估。

### JD 定制简历

粘贴真实 JD，实时生成针对性简历。系统解析 JD 需求、匹配你的职业资产、输出定制版本和投递建议。

## 架构

```
                         ┌──────────────────────────┐
                         │      Frontend (React)      │
                         │  Dashboard / Roles / ...    │
                         └─────────────┬──────────────┘
                                       │ REST API
                         ┌─────────────▼──────────────┐
                         │      Backend (FastAPI)        │
                         │    API Routes / Services      │
                         └─────────────┬──────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                         │                         │
    ┌─────────▼──────┐      ┌──────────▼──────────┐   ┌─────────▼──────┐
    │ Agent 层        │      │   MCP Server         │   │   PostgreSQL   │
    │ (LangGraph)     │      │   (CareerAgent API)  │   │   + Redis      │
    │ 7 个 AI Agent   │      │   Claude Code 工具    │   │                │
    └────────────────┘      └─────────────────────┘   └────────────────┘
```

### 三个入口

| 入口 | 方式 | 适合场景 |
|---|---|---|
| **Web 界面** | `http://localhost:5173` | 完整管理、Dashboard、JD 定制 |
| **Claude Code Skill** | `/check-work` 命令 | 将代码工作转化为成果 |
| **MCP Server** | 8 个工具通过 `.mcp.json` | 自定义集成和自动化 |

### Agent 流水线

```
流水线 1：成果沉淀
  成果录入 → 成果分析 → 岗位匹配 → 简历更新建议 + Gap更新 → 可解释摘要

流水线 2：岗位初始化
  新增岗位 → 能力建模 → 简历骨架生成 → 初始Gap列表 → 初始化摘要

流水线 3：JD 定制
  输入JD → JD解析 → JD评审 → 关键词提取 → 简历生成 → 验证 → 投递建议
```

## 快速开始

### 前置条件

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- 至少一个 LLM API Key（见下方配置说明）

### 安装

```bash
# 1. 克隆
git clone https://github.com/qs-ftw/oh-my-career-agent.git
cd oh-my-career-agent

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env — 填入你的 API Key 和数据库连接

# 3. 配置模型
# config.yaml 已提供默认配置，根据你的 API Key 调整
# 详见下方"配置说明"

# 4. 启动基础设施
docker compose up -d postgres redis

# 5. 启动应用
make dev
```

前端界面：`http://localhost:5173`，API 文档：`http://localhost:8000/docs`。

## 配置说明

项目使用两个配置文件配合工作：

### `.env` — 环境变量

存放密钥和基础设施配置。从 `.env.example` 复制后填入：

| 变量 | 必填 | 说明 |
|---|---|---|
| `DATABASE_URL` | 是 | PostgreSQL 连接字符串 |
| `REDIS_URL` | 是 | Redis 连接字符串 |
| `GLM_API_KEY` | 使用 GLM 模型时 | 智谱 AI (BigModel) API Key |
| `ANTHROPIC_API_KEY` | 使用 Claude 模型时 | Anthropic API Key |
| `INFINI_API_KEY` | 使用 Infini 模型时 | Infini AI 平台 API Key |
| `LANGSMITH_API_KEY` | 否 | LangSmith 追踪 Key |
| `LANGSMITH_TRACING` | 否 | 启用 Agent 追踪（`true`/`false`） |
| `APP_ENV` | 否 | `development` 或 `production` |
| `APP_PORT` | 否 | 后端端口（默认 `8000`） |
| `FRONTEND_URL` | 否 | 前端地址，用于 CORS 配置 |

### `config.yaml` — 模型与 Agent 配置

控制可用的 LLM 模型，以及每个 AI Agent 使用哪个模型。

#### `models` 段 — 定义 LLM 提供商

每个条目定义一个可引用的模型：

```yaml
models:
  my-glm:
    provider: openai_compatible    # "openai_compatible" 或 "anthropic"
    base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: ${GLM_API_KEY}        # 从 .env 中读取
    model: glm-4-flash
    temperature: 0.3
```

| 字段 | 说明 |
|---|---|
| `provider` | `openai_compatible`（兼容 OpenAI 接口的 API）或 `anthropic` |
| `base_url` | API 地址（`openai_compatible` 必填） |
| `api_key` | API Key，支持 `${ENV_VAR}` 语法引用 `.env` 中的变量 |
| `model` | 提供商要求的模型标识符 |
| `temperature` | 采样温度（0.0–1.0） |

默认配置已包含智谱 GLM、Infini Kimi 和 Anthropic Claude。根据你拥有的 API Key 添加或删除条目即可。

#### `agents` 段 — 为 Agent 分配模型

将每个 AI Agent 映射到 `models` 段中定义的模型名称：

```yaml
agents:
  # 简单提取/打分 — 便宜快速就够用
  achievement_analysis: glm-4.5-air
  gap_evaluation: glm-4.5-air

  # 复杂生成任务 — 需要更强的推理能力
  jd_tailoring: glm-5-turbo
  resume_init: glm-5-turbo
  interactive_analysis: glm-5-turbo
```

**可用 Agent 列表：**

| Agent | 功能 | 推荐等级 |
|---|---|---|
| `achievement_analysis` | 分析工作成果 | 轻量 |
| `role_matching` | 将成果匹配到目标岗位 | 轻量 |
| `gap_evaluation` | 评估技能差距 | 轻量 |
| `explain` | 生成可解释摘要 | 轻量 |
| `jd_parsing` | 解析职位描述 | 轻量 |
| `capability_modeling` | 构建岗位能力模型 | 轻量 |
| `resume_update` | 生成简历更新建议 | 轻量 |
| `resume_import` | 从上传的简历中提取数据 | 轻量 |
| `jd_keyword_extract` | 从 JD 中提取关键词 | 轻量 |
| `project_selection` | 为定制简历选择项目 | 轻量 |
| `keyword_verification` | 验证关键词覆盖度 | 轻量 |
| `jd_tailoring` | 针对特定 JD 定制简历 | 强力 |
| `resume_init` | 生成简历初始骨架 | 强力 |
| `resume_generation` | 生成完整定制简历 | 强力 |
| `interactive_analysis` | 深度教练式分析 | 强力 |

**建议：** 提取和打分类任务使用便宜快速的模型。将强力模型留给复杂生成任务（如 `jd_tailoring`、`interactive_analysis`）。

### 启用 `/check-work` 命令

在 Claude Code 中将代码工作直接转化为成果：

1. 安装 MCP Server 依赖：

```bash
cd mcp/careeragent-mcp && pip install -e . && cd ../..
```

2. 项目根目录已包含 `.mcp.json` 配置，Claude Code 会自动检测。

3. 启动后端后，在 Claude Code 中运行：

```
/check-work
```

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端 | Python 3.11+, FastAPI |
| Agent 框架 | LangGraph |
| LLM 提供商 | OpenAI, Anthropic, Google Gemini |
| 数据库 | PostgreSQL |
| 前端 | React 19, Vite, TypeScript |
| UI | Tailwind CSS, Shadcn UI |
| MCP Server | Python FastMCP, httpx |
| 部署 | Docker, docker-compose |

## 开发

```bash
make dev              # 启动所有服务
make dev-backend      # 仅后端（uvicorn 热重载）
make dev-frontend     # 仅前端（Vite dev server）
make test             # 运行所有测试
make lint             # 代码规范检查
make db-migrate       # 运行数据库迁移
make db-seed          # 加载示例数据
```

### 项目结构

```
oh-my-career-agent/
├── backend/                  # FastAPI 后端
│   ├── src/
│   │   ├── api/              # REST 路由
│   │   ├── agent/            # LangGraph Agent 层（7 个 Agent，3 条流水线）
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应 Schema
│   │   ├── services/         # 业务逻辑
│   │   └── core/             # 配置、数据库、LLM、安全
│   └── alembic/              # 数据库迁移
├── frontend/                 # React 前端
│   └── src/
│       ├── pages/            # Dashboard、Roles、Achievements、Gaps、JD Tailor
│       ├── components/       # Shadcn UI + 自定义组件
│       └── hooks/            # TanStack Query hooks
├── mcp/careeragent-mcp/      # Claude Code 的 MCP Server
│   └── src/careeragent_mcp/
│       ├── server.py         # 8 个 MCP 工具
│       └── client.py         # CareerAgent HTTP 客户端
├── .claude/skills/check-work/  # /check-work skill 定义
├── .mcp.json                 # MCP Server 注册配置
└── docs/                     # 设计文档和计划
```

## 路线图

- [x] 项目脚手架、Docker 配置、数据库模型、CI 流水线
- [x] 岗位管理、简历生成、Gap 追踪
- [x] 成果流水线（分析、匹配、建议）
- [x] JD 定制流水线（解析、关键词提取、定制）
- [x] MCP Server + `/check-work` skill 代码转成果
- [ ] 交互式分析（教练风格成果丰富化）
- [ ] PDF 简历导出
- [ ] 面试故事库（STAR+R 结构化准备）
- [ ] 多用户认证

## 参与贡献

欢迎各种形式的贡献。详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

Bug 报告和功能建议：[提交 Issue](https://github.com/qs-ftw/oh-my-career-agent/issues/new)。

## 许可证

[MIT](./LICENSE)

## 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent 工作流编排
- [FastAPI](https://fastapi.tiangolo.com/) — 异步 Python Web 框架
- [Shadcn UI](https://ui.shadcn.com/) — 高质量 React 组件
- [TanStack Query](https://tanstack.com/query/) — 服务端状态管理
- [Model Context Protocol](https://modelcontextprotocol.io/) — MCP 工具标准

---

<div align="center">

**如果这个项目对你有帮助，欢迎给个 Star**

[⭐ Star on GitHub](https://github.com/qs-ftw/oh-my-career-agent)

</div>
