# Check-Work MCP Server + Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 MCP Server + Skill，让用户在 Claude Code 中通过 `/check-work` 将代码成果转化为 Achievement 发布到 CareerAgent。

**Architecture:** MCP Server 作为薄层 API 客户端（Python FastMCP + httpx），封装 CareerAgent REST API 为 MCP 工具。Skill 作为指令文件引导 Claude 完成上下文收集、初稿生成、交互编辑、深度分析、确认发布的完整流程。

**Tech Stack:** Python 3.11+, `mcp` package (FastMCP), `httpx`, `pydantic`

**Design Spec:** `docs/superpowers/specs/2026-04-17-check-work-mcp-skill-design.md`

---

## File Structure

```
mcp/careeragent-mcp/
├── pyproject.toml                          # 依赖声明
└── src/
    └── careeragent_mcp/
        ├── __init__.py                     # 版本号
        ├── server.py                       # FastMCP 服务 + 所有工具定义
        └── client.py                       # CareerAgent HTTP 客户端

.claude/skills/check-work/
└── SKILL.md                               # /check-work 指令文件
```

---

### Task 1: MCP Server 项目脚手架

**Files:**
- Create: `mcp/careeragent-mcp/pyproject.toml`
- Create: `mcp/careeragent-mcp/src/careeragent_mcp/__init__.py`
- Create: `mcp/careeragent-mcp/src/careeragent_mcp/client.py`
- Create: `mcp/careeragent-mcp/src/careeragent_mcp/server.py`

- [ ] **Step 1: 创建项目目录结构**

```bash
mkdir -p mcp/careeragent-mcp/src/careeragent_mcp
```

- [ ] **Step 2: 创建 pyproject.toml**

Create `mcp/careeragent-mcp/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "careeragent-mcp"
version = "0.1.0"
description = "MCP server exposing CareerAgent API as tools for Claude Code"
requires-python = ">=3.11"

dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: 创建 \_\_init\_\_.py**

Create `mcp/careeragent-mcp/src/careeragent_mcp/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: 创建 HTTP 客户端 client.py**

Create `mcp/careeragent-mcp/src/careeragent_mcp/client.py`:

```python
"""Thin async HTTP client for the CareerAgent FastAPI backend."""

import os
from typing import Any

import httpx


class CareerAgentClient:
    """Async HTTP client wrapping CareerAgent REST API calls."""

    def __init__(self) -> None:
        self.base_url = os.environ.get(
            "CAREERAGENT_API_URL", "http://localhost:8000"
        ).rstrip("/")

    async def get(self, path: str, params: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.get(f"/api{path}", params=params)
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, json: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.post(f"/api{path}", json=json)
            resp.raise_for_status()
            # Some endpoints return 204 No Content
            if resp.status_code == 204:
                return None
            return resp.json()

    async def patch(self, path: str, json: dict | None = None) -> Any:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.patch(f"/api{path}", json=json)
            resp.raise_for_status()
            return resp.json()

    async def delete(self, path: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            resp = await client.delete(f"/api{path}")
            resp.raise_for_status()
```

- [ ] **Step 5: 创建 MCP Server 骨架 server.py**

Create `mcp/careeragent-mcp/src/careeragent_mcp/server.py`:

```python
"""CareerAgent MCP Server — exposes CareerAgent REST API as MCP tools."""

from mcp.server.fastmcp import FastMCP

from .client import CareerAgentClient

mcp = FastMCP("CareerAgent")
_client = CareerAgentClient()


# --- Tool definitions will be added here ---


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 6: 验证 MCP Server 可启动**

```bash
cd mcp/careeragent-mcp && pip install -e . && python -m careeragent_mcp.server
```

Expected: Server starts without import errors. Use Ctrl+C to stop.

- [ ] **Step 7: Commit**

```bash
git add mcp/careeragent-mcp/
git commit -m "feat(mcp): scaffold CareerAgent MCP server project"
```

---

### Task 2: Achievement 工具

**Files:**
- Modify: `mcp/careeragent-mcp/src/careeragent_mcp/server.py`

- [ ] **Step 1: 添加 career_create_achievement 工具**

在 `server.py` 的 `# --- Tool definitions will be added here ---` 位置替换为：

```python
# --- Achievement tools ---


@mcp.tool()
async def career_create_achievement(
    title: str,
    raw_content: str,
    tags: list[str] | None = None,
    project_id: str | None = None,
    work_experience_id: str | None = None,
    education_id: str | None = None,
    source_type: str = "code_session",
    date_occurred: str | None = None,
) -> str:
    """Create a new achievement in CareerAgent.

    Args:
        title: Achievement title (max 512 chars).
        raw_content: Detailed description of the achievement.
        tags: Optional list of skill/technology tags.
        project_id: Optional UUID of the project to associate.
        work_experience_id: Optional UUID of the work experience to associate.
        education_id: Optional UUID of the education to associate.
        source_type: Source type, defaults to "code_session".
        date_occurred: Optional date string (YYYY-MM-DD).
    """
    payload: dict = {
        "title": title,
        "raw_content": raw_content,
        "source_type": source_type,
    }
    if tags is not None:
        payload["tags"] = tags
    if project_id is not None:
        payload["project_id"] = project_id
    if work_experience_id is not None:
        payload["work_experience_id"] = work_experience_id
    if education_id is not None:
        payload["education_id"] = education_id
    if date_occurred is not None:
        payload["date_occurred"] = date_occurred

    result = await _client.post("/achievements", json=payload)
    return f"Achievement created: id={result['id']}, title={result['title']}"
```

- [ ] **Step 2: 添加 career_list_achievements 工具**

```python
@mcp.tool()
async def career_list_achievements(
    status: str | None = None,
    project_id: str | None = None,
) -> str:
    """List achievements from CareerAgent.

    Args:
        status: Optional status filter (raw, analyzed, processed).
        project_id: Optional UUID filter for a specific project.
    """
    params: dict = {}
    if status is not None:
        params["status"] = status
    if project_id is not None:
        params["project_id"] = project_id

    results = await _client.get("/achievements", params=params or None)
    if not results:
        return "No achievements found."

    lines = []
    for a in results:
        proj = f" [project={a.get('project_id', '-')}]" if a.get("project_id") else ""
        lines.append(f"- {a['id']}: {a['title']} (status={a['status']}){proj}")
    return "\n".join(lines)
```

- [ ] **Step 3: 添加 career_get_achievement 工具**

```python
@mcp.tool()
async def career_get_achievement(achievement_id: str) -> str:
    """Get a single achievement's full details.

    Args:
        achievement_id: UUID of the achievement.
    """
    result = await _client.get(f"/achievements/{achievement_id}")
    import json

    return json.dumps(result, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 添加 career_update_achievement 工具**

```python
@mcp.tool()
async def career_update_achievement(
    achievement_id: str,
    title: str | None = None,
    raw_content: str | None = None,
    tags: list[str] | None = None,
    project_id: str | None = None,
    parsed_data: dict | None = None,
    importance_score: float | None = None,
) -> str:
    """Update an existing achievement.

    Args:
        achievement_id: UUID of the achievement to update.
        title: Optional new title.
        raw_content: Optional new raw content.
        tags: Optional new tags list.
        project_id: Optional new project UUID to associate.
        parsed_data: Optional structured analysis data to store.
        importance_score: Optional importance score (0.0-1.0).
    """
    payload: dict = {}
    if title is not None:
        payload["title"] = title
    if raw_content is not None:
        payload["raw_content"] = raw_content
    if tags is not None:
        payload["tags"] = tags
    if project_id is not None:
        payload["project_id"] = project_id
    if parsed_data is not None:
        payload["parsed_data"] = parsed_data
    if importance_score is not None:
        payload["importance_score"] = importance_score

    result = await _client.patch(f"/achievements/{achievement_id}", json=payload)
    return f"Achievement updated: id={result['id']}, title={result['title']}"
```

- [ ] **Step 5: 验证 Server 可启动且工具已注册**

```bash
cd mcp/careeragent-mcp && python -c "from careeragent_mcp.server import mcp; print('Tools:', [t.name for t in mcp._tool_manager.tools.values()])"
```

Expected: 输出包含 `career_create_achievement`, `career_list_achievements`, `career_get_achievement`, `career_update_achievement`

- [ ] **Step 6: Commit**

```bash
git add mcp/careeragent-mcp/
git commit -m "feat(mcp): add achievement CRUD tools"
```

---

### Task 3: Project、Role、WorkExperience 工具

**Files:**
- Modify: `mcp/careeragent-mcp/src/careeragent_mcp/server.py`

- [ ] **Step 1: 添加 career_create_project 工具**

在 `server.py` Achievement 工具之后添加：

```python
# --- Project tools ---


@mcp.tool()
async def career_create_project(
    name: str,
    description: str = "",
    tech_stack: list[str] | None = None,
    url: str = "",
    work_experience_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """Create a new project in CareerAgent.

    Args:
        name: Project name (max 200 chars).
        description: Optional project description.
        tech_stack: Optional list of technologies used.
        url: Optional project URL.
        work_experience_id: Optional UUID of associated work experience.
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).
    """
    payload: dict = {"name": name, "description": description, "url": url}
    if tech_stack is not None:
        payload["tech_stack"] = tech_stack
    if work_experience_id is not None:
        payload["work_experience_id"] = work_experience_id
    if start_date is not None:
        payload["start_date"] = start_date
    if end_date is not None:
        payload["end_date"] = end_date

    result = await _client.post("/projects", json=payload)
    return f"Project created: id={result['id']}, name={result['name']}"
```

- [ ] **Step 2: 添加 career_list_projects 工具**

```python
@mcp.tool()
async def career_list_projects() -> str:
    """List all projects from CareerAgent."""
    results = await _client.get("/projects")
    if not results:
        return "No projects found."

    lines = []
    for p in results:
        tech = ", ".join(p.get("tech_stack", []))
        lines.append(f"- {p['id']}: {p['name']} [tech: {tech}]")
    return "\n".join(lines)
```

- [ ] **Step 3: 添加 career_list_roles 工具**

```python
# --- Role tools ---


@mcp.tool()
async def career_list_roles() -> str:
    """List all target roles from CareerAgent."""
    results = await _client.get("/roles")
    if not results:
        return "No target roles configured. Create roles in the CareerAgent web UI first."

    lines = []
    for r in results:
        lines.append(f"- {r['id']}: {r.get('title', r.get('name', 'Unknown'))}")
    return "\n".join(lines)
```

- [ ] **Step 4: 添加 career_list_work_experiences 工具**

```python
# --- Work experience tools ---


@mcp.tool()
async def career_list_work_experiences() -> str:
    """List all work experiences from CareerAgent."""
    results = await _client.get("/work-experiences")
    if not results:
        return "No work experiences found."

    lines = []
    for w in results:
        company = w.get("company", "Unknown")
        title = w.get("title", w.get("position", ""))
        lines.append(f"- {w['id']}: {title} @ {company}")
    return "\n".join(lines)
```

- [ ] **Step 5: 验证所有工具已注册**

```bash
cd mcp/careeragent-mcp && python -c "from careeragent_mcp.server import mcp; tools = [t.name for t in mcp._tool_manager.tools.values()]; print(f'{len(tools)} tools:'); print('\n'.join(f'  - {t}' for t in tools))"
```

Expected: 8 个工具全部列出

- [ ] **Step 6: Commit**

```bash
git add mcp/careeragent-mcp/
git commit -m "feat(mcp): add project, role, and work experience tools"
```

---

### Task 4: Skill `/check-work` 指令文件

**Files:**
- Create: `.claude/skills/check-work/SKILL.md`

- [ ] **Step 1: 创建 Skill 目录**

```bash
mkdir -p .claude/skills/check-work
```

- [ ] **Step 2: 创建 SKILL.md**

Create `.claude/skills/check-work/SKILL.md`:

```markdown
---
name: check-work
description: Convert completed code work into a CareerAgent achievement with deep local analysis. Trigger: /check-work
trigger: /check-work
---

# /check-work

Review your recent code work, generate an achievement draft, interactively refine it, run deep local analysis, and publish to CareerAgent.

## Prerequisites

Before starting, verify:
1. CareerAgent MCP server is connected (try calling `career_list_projects`)
2. CareerAgent backend is running at `localhost:8000`
3. You are in a git repository

If MCP tools are unavailable, tell the user: "CareerAgent MCP 服务未连接。请先启动后端并注册 MCP 服务。"

## Flow

### Phase 1: Context Collection

**If there are new commits in this session:**

1. Run `git log --oneline -20` to see recent commits
2. Run `git diff HEAD~N..HEAD --stat` (where N is the number of new commits) to see change summary
3. Run `git diff HEAD~N..HEAD` to see the actual changes (truncate if too large)
4. Review the current conversation to extract: requirements background, technical decisions, problem-solving approach

**If there are no new commits:**

Tell the user there are no new code changes, then ask what they'd like to do:

> "当前没有新的代码提交。你想要：\n> 1. 选择项目中的某个模块/功能，整理其开发历程为成果\n> 2. 回顾最近的工作经历，手动描述成果\n> 3. 查看最近的 commits 历史，选择一个时间范围来整理"

Based on their choice, gather context accordingly:
- Option 1: Ask which module/feature, then explore its code and git history
- Option 2: Ask the user to describe their work in their own words
- Option 3: Show `git log --oneline -30`, let user pick a range, then analyze those commits

### Phase 2: Achievement Draft Generation

Synthesize all gathered context into an achievement draft. Output it in this format:

```
## 成果初稿

**标题**: [一句话概括，突出核心价值]

**原始内容**:
[Situation] ...
[Task] ...
[Action] ...
[Result] ...

**技术标签**: [tag1, tag2, ...]

**技术栈**: [tech1, tech2, ...]
```

Rules:
- Title: concise, highlight core value (e.g., "实现教育模块的级联删除与 Markdown 导出")
- Raw content: follow STAR method, weave in decision context from conversation
- Tags: extract technical keywords from code diff and conversation
- Source type: always `code_session`

### Phase 3: Interactive Editing

Present the draft and ask:

> "以上是根据你的工作自动生成的成果初稿。你觉得如何？需要调整哪些部分？"

Then enter an interactive refinement loop:
1. If user wants to change specific fields, edit them and re-show
2. If user provides additional information, incorporate it
3. Ask follow-up questions to enrich the content (STAR gaps)
4. Use encouraging, warm tone (career coach style) but keep it concise for terminal

Follow-up questions to consider (pick 1-2 most relevant, not all):
- "这个工作的背景/业务场景是什么？"
- "你解决了什么核心问题？为什么重要？"
- "方案设计时考虑了哪些替代方案？为什么选了这个？"
- "有没有可量化的成果？（性能提升、bug减少、用户影响等）"

Continue until the user is satisfied or says "OK"/"可以了"/"够了".

### Phase 4: Deep Local Analysis

Run four analysis dimensions. Present results as a structured card.

#### 4a. Technical Analysis

Based on the code changes and conversation context, identify:
- Technologies and architectural patterns used
- Core technical decisions and their rationale
- Complex problems solved and solutions adopted

Output format:
```
### 技术分析

**技术要点**:
- point 1
- point 2

**挑战与方案**:
- 挑战: ... → 方案: ...

**架构决策**:
- decision: why it was chosen
```

#### 4b. Capability Analysis

From the conversation and code, identify demonstrated soft skills:
- Problem analysis and diagnosis
- Solution design and evaluation
- Technical leadership and decision-making
- Collaboration and communication

Output format:
```
### 能力分析

**体现的能力**:
- [capability]: evidence from the work

**面试要点**:
- 面试中可以这样表述: ...
```

#### 4c. Project Association

1. Call `career_list_projects` MCP tool to get existing projects
2. Based on code change paths and tech stack, suggest the best matching project
3. If no match, suggest creating a new project with auto-filled fields

Present to user:
```
### 项目关联

**推荐关联到**: [project name] (id: xxx)
理由: ...

或者 [新建项目]:
- 名称: ...
- 描述: ...
- 技术栈: ...
```

Ask user to confirm or adjust.

#### 4d. Role Matching

1. Call `career_list_roles` MCP tool to get target roles
2. Analyze achievement content against each role
3. Only include roles with match_score >= 0.3

Present to user:
```
### 角色匹配

- **[Role name]**: 匹配度 0.8 — 原因: ...
- **[Role name]**: 匹配度 0.5 — 原因: ...
```

### Phase 5: Review and Publish

Show the final achievement card:

```
## 最终成果

**标题**: ...
**关联项目**: ...
**标签**: ...
**技术栈**: ...
**来源**: code_session

**内容**:
...

**分析数据**:
- 技术要点: ...
- 挑战与方案: ...
- 能力标签: ...
- 角色匹配: ...

确认发布到 CareerAgent？(yes/no)
```

If user confirms:
1. If creating a new project: call `career_create_project` first, get the project_id
2. Call `career_create_achievement` with all fields
3. Call `career_update_achievement` to store analysis results as `parsed_data`

On success, report:
> "成果已发布！Achievement ID: {id}"

## Error Handling

| Scenario | Action |
|----------|--------|
| MCP tools unavailable | Tell user to start MCP server and backend |
| Backend unreachable | Tell user to start CareerAgent backend (`make dev` or `docker-compose up`) |
| Not a git repo | Tell user this command only works in git repositories |
| API returns 404/422 | Show the error details and suggest checking the data |
```

- [ ] **Step 3: 验证 Skill 文件格式正确**

```bash
head -5 .claude/skills/check-work/SKILL.md
```

Expected: 显示 YAML frontmatter with name, description, trigger

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/check-work/
git commit -m "feat(skill): add /check-work skill for code-to-achievement conversion"
```

---

### Task 5: 注册 MCP Server 到 Claude Code

**Files:**
- Modify: `.claude/settings.local.json`

- [ ] **Step 1: 添加 MCP Server 配置到 settings.local.json**

在 `.claude/settings.local.json` 中添加 `mcpServers` 配置。读取当前文件内容，然后添加：

在 JSON 的顶层添加 `mcpServers` 键（与 `env`、`permissions` 平级）：

```json
"mcpServers": {
  "careeragent": {
    "command": "python",
    "args": ["mcp/careeragent-mcp/src/careeragent_mcp/server.py"],
    "cwd": "/Users/gaoqiangsheng/work/playground/CareerAgent"
  }
}
```

- [ ] **Step 2: 验证配置格式正确**

```bash
python -c "import json; json.load(open('.claude/settings.local.json')); print('JSON valid')"
```

Expected: `JSON valid`

- [ ] **Step 3: Commit**

```bash
git add .claude/settings.local.json
git commit -m "feat(mcp): register CareerAgent MCP server in Claude Code settings"
```

---

### Task 6: 端到端验证

**Files:** 无新文件

- [ ] **Step 1: 安装 MCP Server 依赖**

```bash
cd mcp/careeragent-mcp && pip install -e . && cd ../..
```

- [ ] **Step 2: 验证 CareerAgent 后端运行中**

```bash
curl -s http://localhost:8000/api/projects | head -100
```

Expected: 返回 JSON 数组（可能为空 `[]`）

如果后端未运行，先启动：
```bash
cd backend && make dev
```

- [ ] **Step 3: 手动测试 MCP Server 工具**

```bash
cd mcp/careeragent-mcp && python -c "
import asyncio
from careeragent_mcp.client import CareerAgentClient

async def test():
    c = CareerAgentClient()
    projects = await c.get('/projects')
    print(f'Projects: {len(projects)} found')
    roles = await c.get('/roles')
    print(f'Roles: {len(roles)} found')
    experiences = await c.get('/work-experiences')
    print(f'Work experiences: {len(experiences)} found')

asyncio.run(test())
"
```

Expected: 打印各资源的数量

- [ ] **Step 4: 重启 Claude Code 并测试 /check-work**

重启 Claude Code 后：
1. 输入 `/check-work`
2. 验证 Skill 被加载
3. 验证 MCP 工具可用

- [ ] **Step 5: Final commit (如果有修复)**

```bash
git add -A
git commit -m "fix: address issues from end-to-end verification"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: 每个设计需求都有对应 Task
  - MCP Server 8 个工具 → Task 2 + Task 3
  - Skill 5 步流程 → Task 4
  - MCP 注册 → Task 5
  - 端到端验证 → Task 6
  - 无 commits 引导 → Task 4 Phase 1
  - 四维度分析 → Task 4 Phase 4
  - 错误处理 → Task 4 Error Handling + client.py
- [x] **Placeholder scan**: 无 TBD/TODO/implement later
- [x] **Type consistency**: 所有 MCP 工具参数与 CareerAgent API schema 一致
  - AchievementCreate 字段匹配 `backend/src/schemas/achievement.py`
  - ProjectCreate 字段匹配 `backend/src/schemas/project.py`
  - API 路径匹配 `backend/src/api/router.py` 的 prefix 结构
