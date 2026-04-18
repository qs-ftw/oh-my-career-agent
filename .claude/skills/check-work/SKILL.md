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

> "当前没有新的代码提交。你想要：
> 1. 选择项目中的某个模块/功能，整理其开发历程为成果
> 2. 回顾最近的工作经历，手动描述成果
> 3. 查看最近的 commits 历史，选择一个时间范围来整理"

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
