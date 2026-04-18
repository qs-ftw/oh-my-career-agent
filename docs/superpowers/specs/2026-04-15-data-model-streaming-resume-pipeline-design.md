# 候选人数据建模 + 流式进度 + 简历深度定制管道 Design Spec

**Date:** 2026-04-15
**Priority Order:** 数据建模 → 流式进度 → 路线B管道
**Approach:** 方案B — 干净重构，零历史包袱，可舍弃旧数据

---

## 1. 候选人数据建模

### 1.1 设计理念

参考 career-ops 的 `cv.md` 结构（Company > Role > Achievements），用数据库实现结构化存储。DB 存核心结构，需要时导出为 Markdown 给 LLM 消费。三层层次 + 灵活关联。

### 1.2 数据层次

```
CareerProfile (每人一个，聚合层)
├── WorkExperience (公司 + 角色)
│   ├── Project (可选，项目)
│   │   └── Achievement (成果)
│   └── Achievement (直接挂在岗位下的成果)
├── Project (独立项目，如开源/个人项目)
│   └── Achievement
└── Achievement (独立成果，如证书、演讲)
```

### 1.3 表结构

#### `career_profiles` — 职业档案（新增）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| user_id | UUID FK→users | |
| workspace_id | UUID FK→workspaces | |
| name | varchar(100) | 姓名 |
| headline | varchar(200) | 一句话定位 |
| email | varchar(200) | |
| phone | varchar(50) | |
| linkedin_url | varchar(500) | |
| portfolio_url | varchar(500) | |
| github_url | varchar(500) | |
| location | varchar(100) | |
| professional_summary | text | 专业总结 |
| skill_categories | JSONB | `{"后端": ["Python","Go"], "前端": ["React"]}` |
| created_at | timestamp | |
| updated_at | timestamp | |

#### `work_experiences` — 工作经历（新增）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| profile_id | UUID FK→career_profiles | ON DELETE CASCADE |
| company_name | varchar(200) | |
| company_url | varchar(500) | |
| location | varchar(100) | |
| role_title | varchar(200) | |
| start_date | date | |
| end_date | date, nullable | null = 至今 |
| description | text | 岗位概述（1-2句） |
| sort_order | int | 展示顺序，默认0 |

#### `projects` — 项目（新增）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| profile_id | UUID FK→career_profiles | ON DELETE CASCADE |
| work_experience_id | UUID FK→work_experiences, nullable | null = 独立项目 |
| name | varchar(200) | |
| description | text | 项目概述 |
| tech_stack | JSONB | `["Python", "Kafka", "K8s"]` |
| url | varchar(500) | 项目链接 |
| start_date | date, nullable | |
| end_date | date, nullable | |
| sort_order | int | |

#### `achievements` — 成果（重构，DROP 旧表重建）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| profile_id | UUID FK→career_profiles | ON DELETE CASCADE |
| project_id | UUID FK→projects, nullable | 所属项目 |
| work_experience_id | UUID FK→work_experiences, nullable | 所属工作经历 |
| title | varchar(512) | |
| raw_content | text | 用户输入的原始文本 |
| parsed_data | JSONB | 分析结果（合并原6个_json字段） |
| tags | JSONB | `["Kafka", "微服务", "性能优化"]` |
| importance_score | float, default 0.0 | |
| source_type | varchar(50), default "manual" | manual / git / slack |
| status | varchar(20), default "raw" | raw / analyzed / applied |
| date_occurred | date, nullable | 成果发生时间 |
| created_at | timestamp | |
| updated_at | timestamp | |

`parsed_data` JSONB 结构：
```json
{
  "summary": "一句话摘要",
  "technical_points": ["点1", "点2"],
  "challenges": ["挑战1"],
  "solutions": ["方案1"],
  "metrics": [{"description": "提升了", "value": "30%"}],
  "interview_points": ["面试要点1"],
  "importance_score": 0.8
}
```

**删除的旧字段**：`parsed_summary`, `technical_points_json`, `challenges_json`, `solutions_json`, `metrics_json`, `interview_points_json` — 全部合并到 `parsed_data`。

#### 保留不变的表

- `resumes` — 保留
- `resume_versions` — 保留
- `target_roles` — 保留
- `update_suggestions` — 保留
- `achievement_resume_links` — 保留，FK 更新指向新 achievements 表

### 1.4 Markdown 导出服务

`CareerMarkdownService.export(profile_id)` 方法，从 DB 数据生成 career-ops 风格的 Markdown：

```markdown
# CV -- 张三

## Contact Info
北京 | zhangsan@email.com | [LinkedIn](...) | [GitHub](...)

## Professional Summary
8年后端经验的资深工程师...

## Work Experience

### 字节跳动 -- 北京
**高级后端工程师** | 2022-03 - Present

**广告投放平台重构**
- 设计并实现基于 Kafka 的实时竞价系统，QPS 提升 300%
- 引入缓存分层策略，P99 延迟从 200ms 降至 50ms
- 技术栈: Go, Kafka, Redis, K8s

## Projects
- **开源工具 X** | GitHub Stars: 500
  一个用于...的工具。技术栈: Rust, WASM

## Skills
- **后端:** Go, Python, Java
- **基础设施:** Kubernetes, Docker, Terraform
- **数据:** Kafka, Redis, PostgreSQL
```

此 Markdown 即为传给 LLM 的 career_assets，人可读、LLM 友好、结构清晰。

### 1.5 Schema 文件变更

- `backend/src/models/` — 新增 `career_profile.py`, `work_experience.py`, `project.py`；重构 `achievement.py`
- `backend/src/schemas/` — 新增对应 Pydantic schema
- `backend/src/services/` — 新增 `career_profile_service.py`，`career_markdown_service.py`
- `backend/alembic/versions/` — 新 migration（DROP 旧 achievements 表，CREATE 四张新表）

---

## 2. 流式进度（SSE + 打字机效果）

### 2.1 设计理念

建通用基础设施，所有长耗时管道（成果分析、JD解析、简历生成）复用。三层：后端 SSE → 前端 Hook → UI 组件。

### 2.2 后端：Pipeline Event Stream

**新增依赖**：`sse-starlette`

**核心机制**：用 LangGraph 的 `astream_events` API 捕获节点生命周期事件，转化为 SSE 事件流。

**SSE 事件协议**：

```
event: node_start
data: {"node": "achievement_analysis", "label": "正在解析成果..."}

event: token
data: {"text": "这段", "node": "achievement_analysis"}

event: token
data: {"text": "经历涉及", "node": "achievement_analysis"}

event: node_complete
data: {"node": "achievement_analysis", "duration_ms": 3200, "summary": "解析完成，提取了5个技术要点"}

event: pipeline_complete
data: {"total_duration_ms": 18500, "result_id": "uuid-xxx"}
```

**新增 API endpoints**：

```
GET /api/achievements/{id}/stream-analysis   → SSE
GET /api/jd/stream-parse                     → SSE
GET /api/resumes/{id}/stream-generate        → SSE
```

每个 endpoint 内部：
1. `astream_events` 运行 LangGraph 管道
2. 过滤 `on_chain_start` / `on_chain_end` / `on_llm_new_token` 事件
3. 映射为 SSE 事件格式
4. yield 给 `EventSourceResponse`

### 2.3 前端：通用 Hook + 组件

**`usePipelineStream` Hook**：

```typescript
interface PipelineEvent {
  type: "node_start" | "token" | "node_complete" | "pipeline_complete";
  node?: string;
  label?: string;
  text?: string;
  duration_ms?: number;
  summary?: string;
  result_id?: string;
}

interface PipelineStep {
  node: string;
  label: string;
  status: "pending" | "running" | "completed";
  tokens: string;        // 累积的 LLM 输出
  duration_ms?: number;
  summary?: string;
}

function usePipelineStream(url: string): {
  start: () => void;
  steps: PipelineStep[];
  isStreaming: boolean;
  resultId: string | null;
  error: string | null;
  cancel: () => void;
}
```

内部用 `fetch` + `ReadableStream` 解析 SSE 文本流（不用 EventSource，因为需要 POST 和自定义 header）。

**`PipelineProgressModal` 组件**：

```
┌─────────────────────────────────────────┐
│  ✅ 成果解析                  3.2s       │
│  ┌─────────────────────────────────┐    │
│  │ 这段经历涉及微服务架构设计，    │    │
│  │ 使用了 gRPC 和 Kafka 实现      │    │
│  │ 服务间通信...                   │    │
│  └─────────────────────────────────┘    │
│                                         │
│  🔄 岗位匹配                  进行中... │
│  ┌─────────────────────────────────┐    │
│  │ 正在对比目标岗位"高级后端工   │    │
│  │ 程师"的技能要求...▌             │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ⏳ 简历更新建议              等待中     │
│  ⏳ 差距评估                  等待中     │
│                                         │
│                     [取消分析]           │
└─────────────────────────────────────────┘
```

- 每个节点一行：图标 + 名称 + 耗时/状态
- 当前节点的 LLM 输出实时滚动显示（打字机效果）
- 完成的节点折叠显示摘要
- 支持取消（关闭 SSE 连接，后端检测断连停止管道）

### 2.4 文件变更

**后端：**
- 新增 `backend/src/api/pipeline_stream.py` — SSE endpoint 集合
- 新增 `backend/src/services/pipeline_stream_service.py` — SSE 事件包装逻辑
- `pyproject.toml` — 添加 `sse-starlette` 依赖

**前端：**
- 新增 `frontend/src/hooks/usePipelineStream.ts` — 通用 SSE hook
- 新增 `frontend/src/components/PipelineProgressModal.tsx` — 进度弹窗组件
- 修改 `Achievements.tsx` — 分析按钮改为触发 SSE + 弹窗

---

## 3. 路线B — 多步简历深度定制管道

### 3.1 管道结构

**当前**（1步粗放）：
```
jd_parsing → jd_tailoring(一把梭) → explain
```

**新管道**（4步精调）：
```
jd_parsing → jd_keyword_extract → project_selection → resume_generation → keyword_verification → explain
```

### 3.2 各节点设计

#### 节点1：`jd_keyword_extract`

**职责**：从 `jd_parsed` 中提取 15-20 个核心关键词，标注权重和类别。

**输入**：`jd_parsed`（已有的解析结果）
**输出**：`jd_keywords`

```json
{
  "keywords": [
    {"keyword": "微服务", "weight": 0.95, "category": "architecture"},
    {"keyword": "Kubernetes", "weight": 0.9, "category": "infrastructure"},
    {"keyword": "高并发", "weight": 0.85, "category": "capability"}
  ],
  "language": "zh",
  "archetype": "backend_infra",
  "experience_level": "senior"
}
```

#### 节点2：`project_selection`

**职责**：从用户 Markdown 简历中，选出与 JD 关键词最匹配的 3-4 个项目和 2-3 段工作经历。

**输入**：`jd_keywords` + Markdown 格式的 career profile
**输出**：`selected_content`

```json
{
  "selected_experiences": [
    {
      "work_experience_id": "uuid",
      "relevance_score": 0.9,
      "selected_projects": ["uuid-1", "uuid-3"],
      "reason": "广告平台重构与JD的微服务+高并发高度匹配"
    }
  ],
  "selected_projects": ["uuid-1", "uuid-3", "uuid-5"],
  "omitted_projects": ["uuid-2", "uuid-4"],
  "coverage_notes": "关键词'Kubernetes'未在选中项目中匹配，需在Summary补充"
}
```

#### 节点3：`resume_generation`

**职责**：基于筛选内容生成完整简历，包含关键词注入。

**输入**：`jd_keywords` + `selected_content` + Markdown career profile
**输出**：`resume_draft`（ResumeContent）

**Prompt 关键指令**：

```
## 关键词注入规则
以下是 JD 的核心关键词（按权重排序）：
{keywords}

要求：
1. Summary 中必须自然融入前 5 个关键词
2. 每段工作经历的第一条 bullet 必须包含一个匹配的关键词
3. Skills 区域必须覆盖所有关键词
4. 只用 JD 的精确词汇重新表述真实经验
5. 绝不能添加候选人没有的技能或经验
```

#### 节点4：`keyword_verification`

**职责**：检查简历中每个 JD 关键词的覆盖情况，未覆盖的给出补丁建议。

**输入**：`jd_keywords` + `resume_draft`
**输出**：`keyword_coverage` + `resume_patches`

```json
{
  "coverage_score": 0.82,
  "covered": [
    {"keyword": "微服务", "location": "summary, experience[0].bullet[1]"}
  ],
  "uncovered": [
    {"keyword": "系统设计", "suggestion": "在经历1的描述中加入'主导系统设计评审'"}
  ],
  "patches": [
    {
      "section": "experiences[0].description",
      "original": "负责后端服务开发",
      "patched": "主导后端系统设计与架构评审，负责核心服务开发",
      "keyword_covered": "系统设计"
    }
  ]
}
```

若 `coverage_score < 0.7`，自动应用 patches 后重新检查一次。

### 3.3 管道状态扩展

`CareerAgentState` 新增：

```python
jd_keywords: dict          # 关键词提取结果
selected_content: dict     # 筛选出的项目/经历
keyword_coverage: dict     # 覆盖率检查结果
resume_patches: list       # 补丁列表
```

### 3.4 与数据建模的衔接

- 新管道的核心输入是 `CareerMarkdownService.export(profile_id)` 生成的 Markdown
- 旧 `jd_tailoring` 节点 → 替换为新的 4 节点管道
- LLM 输出的简历内容存入 `ResumeVersion.content_json`

### 3.5 文件变更

**后端：**
- 新增 `backend/src/agent/nodes/jd_keyword_extract.py`
- 新增 `backend/src/agent/nodes/project_selection.py`
- 新增 `backend/src/agent/nodes/resume_generation.py`
- 新增 `backend/src/agent/nodes/keyword_verification.py`
- 修改 `backend/src/agent/state.py` — 新增 state 字段
- 修改 `backend/src/agent/graphs/` — 更新 JD 管道图定义
- 旧 `jd_tailoring.py` → 删除或标记废弃

---

## 实施顺序

1. **Phase 1 — 数据建模**（基础，其他都依赖它）
   - 新建 `career_profiles`, `work_experiences`, `projects` 表
   - 重构 `achievements` 表
   - 实现 `CareerMarkdownService`
   - 前端：职业档案管理页面 + 工作经历/项目/成果 CRUD

2. **Phase 2 — 流式进度**（相对独立）
   - 后端 SSE 基础设施
   - 前端 `usePipelineStream` hook
   - 前端 `PipelineProgressModal` 组件
   - 接入成果分析流程

3. **Phase 3 — 路线B管道**（依赖 Phase 1 的数据模型）
   - 4 个新管道节点
   - 更新 JD 管道图
   - 接入流式进度
   - 前端适配新管道输出
