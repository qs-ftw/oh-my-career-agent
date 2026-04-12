<div align="center">

# CareerAgent

**面向长期求职的 Agent 自动化简历构建服务**

长期职业资产管理系统 -- 把真实工作成果持续转化为岗位定制简历、能力 Gap 分析与 JD 现场定制方案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![GitHub Stars](https://img.shields.io/github/stars/your-username/CareerAgent?style=social)](https://github.com/your-username/CareerAgent)
[![GitHub Issues](https://img.shields.io/github/issues/your-username/CareerAgent)](https://github.com/your-username/CareerAgent/issues)

[English](./README.md) | **中文**

</div>

---

## 目录

- [项目简介](#项目简介)
- [核心亮点](#核心亮点)
- [功能特性](#功能特性)
- [架构概览](#架构概览)
- [快速开始](#快速开始)
- [开发指南](#开发指南)
- [技术栈](#技术栈)
- [开发路线图](#开发路线图)
- [参与贡献](#参与贡献)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 项目简介

CareerAgent 不是一个"一次性写简历"的工具，而是一套 **长期运行的职业资产管理系统**，专为有长期求职规划的软件工程师设计。

当你同时准备多个技术方向（Agent 开发工程师、算法工程师、后端工程师、量化开发等），面临多份版本化简历维护困难、日常成果难以沉淀、能力 Gap 模糊不清、面对真实 JD 无法快速定制等问题时，CareerAgent 通过 AI Agent 自动化帮你解决这些痛点。

系统的核心理念是：

> **把长期求职这件事，做成一个持续运行的 Agent 系统。**

它同时解决三件事：

1. **长期记忆** -- 记住你想投的岗位，为每个方向维护独立简历
2. **持续沉淀** -- 把真实项目成果自动转化为职业资产
3. **现场应对** -- 面对真实 JD，快速生成定制化版本并评估匹配度

---

## 核心亮点

- **Agent 驱动，而非模板驱动** -- 7 个专业 AI Agent 协同工作，不是简单的关键词替换
- **长期记忆系统** -- 跨岗位、跨版本的职业资产持续积累，越用越丰富
- **真实成果驱动** -- 所有简历内容来源于真实项目产出，拒绝虚构包装
- **可解释、可控、可回滚** -- Agent 每一步操作都有原因说明，用户可确认、编辑、拒绝和回滚

---

## 功能特性

### 🎯 长期多岗位目标管理

同时维护多个求职方向的定制化简历（如 Agent 开发工程师、算法工程师、后端工程师、量化开发等）。每个岗位拥有独立的能力模型、主简历版本和 Gap 列表。系统长期记住你的求职方向，持续追踪每个岗位的准备进度。

### 📦 成果自动沉淀

将日常工作成果（代码、项目、milestone、性能优化、技术攻坚）自动分析并转化为简历内容。Achievement Analysis Agent 提取技术亮点、难点、指标收益和面试可展开点，自动判断成果适合哪些目标岗位，生成定向简历更新建议。

### 📊 能力 Gap 分析

结构化分析当前能力与目标岗位的差距，区分"完全缺失"、"有能力但无证据"、"表达弱"、"缺乏量化"等不同 Gap 类型。自动生成优先级排序的补齐计划，追踪每个 Gap 的进度变化，让你明确知道先补什么最划算。

### 📋 JD 现场定制

输入真实岗位 JD，实时生成针对性简历并评估匹配度。支持两种模式：从职业资产池全新生成，或基于已有主简历定向微调。输出能力匹配度、简历表达匹配度、投递准备度三维度评分，并给出"建议直接投 / 微调后投 / 补齐后投 / 暂不建议投"的明确建议。

---

## 架构概览

CareerAgent 采用 **模块化单体架构 + Agent 工作流编排** 的设计：

```
                          ┌─────────────────────────┐
                          │      Frontend (React)    │
                          │  Dashboard / Roles / ...  │
                          └────────────┬──────────────┘
                                       │ REST API
                          ┌────────────▼──────────────┐
                          │      Backend (FastAPI)      │
                          │   API Routes / Services     │
                          └────────────┬──────────────┘
                                       │
                          ┌────────────▼──────────────┐
                          │   Agent Layer (LangGraph)   │
                          │  7 专业 Agent / 3 核心流水线  │
                          └────────────┬──────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
          ┌─────────▼──────┐ ┌────────▼────────┐ ┌───────▼───────┐
          │  PostgreSQL     │ │   Multi-LLM     │ │    Redis      │
          │  (16 tables)    │ │  OpenAI/Claude/  │ │   (Cache)     │
          │                 │ │  Gemini          │ │               │
          └────────────────┘ └─────────────────┘ └───────────────┘
```

### 7 个专业 AI Agent

| Agent | 职责 |
|-------|------|
| Achievement Analysis Agent | 解析原始成果，提取技术亮点、难点、指标、面试点 |
| Role Matching Agent | 判断成果与哪些目标岗位相关，输出匹配分数和原因 |
| Resume Update Agent | 生成简历段落级更新建议，控制表达风格与关键词策略 |
| Gap Evaluation Agent | 更新 Gap 状态，关闭已补齐项，新建新 Gap，调整优先级 |
| JD Parsing Agent | 解析真实 JD，提取必备技能、关键词、风格偏好 |
| JD Tailoring Agent | 基于 JD 生成定制简历，输出匹配度评估和投递建议 |
| Explain Agent | 把系统判断转为用户可读解释，保证产品不是黑盒 |

### 3 条核心流水线

```
流水线 1：成果沉淀
  成果录入 → [成果分析] → [岗位匹配] → [简历更新建议] + [Gap更新] → [可解释摘要] → 用户确认

流水线 2：岗位初始化
  新增岗位 → [能力建模] → [简历骨架生成] → [初始Gap列表] → [初始化摘要]

流水线 3：JD 定制
  输入JD → [JD解析] → 模式分支(全新生成/微调现有) → [JD定制] → [匹配评分] → [投递建议]
```

---

## 快速开始

### 前置条件

- [Python](https://www.python.org/) 3.11+
- [Node.js](https://nodejs.org/) 18+
- [Docker](https://www.docker.com/) & Docker Compose
- [Make](https://www.gnu.org/software/make/)（macOS / Linux 自带）
- 至少一个 LLM API Key（OpenAI / Anthropic / Google Gemini）

### 安装步骤

**1. 克隆仓库**

```bash
git clone https://github.com/your-username/CareerAgent.git
cd CareerAgent
```

**2. 配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key 和数据库配置：

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/careeragent

# LLM Providers (至少配置一个)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Redis
REDIS_URL=redis://localhost:6379/0

# App
APP_ENV=development
APP_PORT=8000
FRONTEND_URL=http://localhost:5173
```

**3. 启动基础设施（PostgreSQL + Redis）**

```bash
docker compose up -d postgres redis
```

**4. 启动开发环境**

```bash
# 一键启动前后端（推荐）
make dev

# 或者分别启动
make dev-backend    # 后端 FastAPI (http://localhost:8000)
make dev-frontend   # 前端 Vite (http://localhost:5173)
```

**5. 初始化数据库**

```bash
make db-migrate     # 运行数据库迁移
make db-seed        # 加载示例数据（可选）
```

**6. 访问应用**

- 前端界面：http://localhost:5173
- 后端 API 文档：http://localhost:8000/docs

---

## 开发指南

### Make 命令速查

```bash
# 开发
make dev              # 启动所有服务（后端 + 前端 + PostgreSQL）
make dev-backend      # 仅启动后端（uvicorn 热重载）
make dev-frontend     # 仅启动前端（vite dev server）

# 测试
make test             # 运行所有测试（后端 + 前端）
make test-backend     # 仅运行后端测试
make test-frontend    # 仅运行前端测试

# 代码质量
make lint             # 检查代码规范（ruff + eslint）
make format           # 自动格式化代码

# 数据库
make db-migrate       # 运行 Alembic 数据库迁移
make db-seed          # 加载开发用示例数据

# 构建
make build            # 生产构建（前端 + 后端 Docker 镜像）
```

### 项目结构

```
CareerAgent/
├── backend/                       # 后端服务
│   ├── src/
│   │   ├── main.py                # FastAPI 应用入口
│   │   ├── api/                   # API 路由处理
│   │   │   ├── roles.py           # 岗位目标 CRUD
│   │   │   ├── resumes.py         # 简历管理
│   │   │   ├── achievements.py    # 成果录入与分析
│   │   │   ├── gaps.py            # Gap 查询与更新
│   │   │   ├── jd.py              # JD 解析与定制
│   │   │   └── suggestions.py     # 更新建议管理
│   │   ├── agent/                 # LangGraph Agent 层
│   │   │   ├── graph.py           # 工作流图定义
│   │   │   ├── state.py           # 状态 Schema (TypedDict)
│   │   │   ├── configuration.py   # Agent 模型配置
│   │   │   ├── nodes/             # Agent 节点实现
│   │   │   │   ├── achievement_analysis.py
│   │   │   │   ├── role_matching.py
│   │   │   │   ├── resume_update.py
│   │   │   │   ├── gap_evaluation.py
│   │   │   │   ├── jd_tailoring.py
│   │   │   │   ├── jd_parsing.py
│   │   │   │   ├── resume_init.py
│   │   │   │   └── explain.py
│   │   │   └── tools/             # Agent 可调用工具
│   │   │       ├── db_query.py
│   │   │       └── scoring.py
│   │   ├── core/                  # 基础设施
│   │   │   ├── config.py          # Pydantic Settings 配置
│   │   │   ├── database.py        # 异步 SQLAlchemy 引擎
│   │   │   ├── llm.py             # 多 LLM Provider 抽象
│   │   │   └── security.py        # 认证辅助（SaaS 预留）
│   │   ├── models/                # SQLAlchemy ORM 模型（16 张表）
│   │   ├── schemas/               # Pydantic 请求/响应 Schema
│   │   ├── prompts/               # 各 Agent 的 Prompt 模板
│   │   └── services/              # 业务逻辑层
│   ├── tests/                     # 测试
│   │   ├── test_api/              # API 端点测试
│   │   ├── test_agent/            # Agent 节点测试
│   │   └── test_services/         # Service 层测试
│   ├── alembic/                   # 数据库迁移
│   ├── pyproject.toml
│   └── langgraph.json
├── frontend/                      # 前端应用
│   ├── src/
│   │   ├── App.tsx                # 路由配置
│   │   ├── components/
│   │   │   ├── ui/                # Shadcn UI 基础组件
│   │   │   ├── layout/            # 布局组件 (Sidebar/Header)
│   │   │   └── shared/            # 通用业务组件
│   │   ├── pages/                 # 页面组件
│   │   │   ├── Dashboard.tsx      # 仪表盘
│   │   │   ├── Roles.tsx          # 岗位列表
│   │   │   ├── ResumeDetail.tsx   # 简历详情
│   │   │   ├── Achievements.tsx   # 成果中心
│   │   │   ├── GapBoard.tsx       # Gap 看板
│   │   │   ├── JDTailor.tsx       # JD 定制
│   │   │   └── Suggestions.tsx    # 更新建议中心
│   │   ├── hooks/                 # TanStack Query Hooks
│   │   ├── lib/                   # 工具函数和 API 客户端
│   │   └── types/                 # TypeScript 类型定义
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── docs/                          # 项目文档
├── docker-compose.yml             # Docker 编排
├── Makefile                       # 开发命令
├── .env.example                   # 环境变量模板
└── LICENSE                        # MIT 许可证
```

---

## 技术栈

| 层级 | 技术 | 说明 |
|:-----|:-----|:-----|
| **后端框架** | Python 3.11+ / FastAPI | 异步 API，LangGraph 兼容，丰富的 AI 生态 |
| **Agent 框架** | LangGraph | 工作流编排，状态管理，流式输出 |
| **LLM** | 多模型支持 (OpenAI, Anthropic, Gemini) | 按 Agent 任务选择最优模型，成本优化 |
| **数据库** | PostgreSQL | 关系型 + JSONB，SaaS 就绪 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 类型安全模型，生产级迁移 |
| **前端框架** | React 19 + Vite + TypeScript | 快速开发体验，强类型保障 |
| **UI 组件库** | Tailwind CSS + Shadcn UI | 一致的设计风格，无障碍组件 |
| **状态管理** | TanStack Query | 服务端状态缓存，乐观更新 |
| **基础设施** | Docker + docker-compose | 本地开发与生产环境一致 |
| **缓存** | Redis | 任务队列与缓存 |
| **CI/CD** | GitHub Actions | 自动化 lint、测试、构建 |

---

## 开发路线图

### Sprint 1: 基础搭建（第 1-2 周）

**目标**：项目骨架在本地跑通，数据库就绪，CI 绿灯。

- [x] Monorepo 目录结构搭建
- [x] Docker Compose 配置（PostgreSQL + Redis）
- [x] Makefile 开发命令
- [x] 后端：FastAPI 应用、16 张 SQLAlchemy 模型、Alembic 迁移、路由桩
- [x] 前端：Vite + React + Tailwind + Shadcn 初始化，路由配置，布局外壳
- [x] 开源文件：双语文档 README、LICENSE、CONTRIBUTING、CODE_OF_CONDUCT
- [x] GitHub Actions CI：lint + 测试

### Sprint 2: 岗位管理 + 简历（第 3-4 周）

**目标**：用户可以创建岗位，查看自动生成的简历和 Gap。

- [ ] 岗位目标 CRUD API + UI
- [ ] 岗位初始化 LangGraph 工作流（能力建模 -> 简历骨架 -> Gap 初始化）
- [ ] 简历查看/编辑 API + UI
- [ ] 简历版本记录
- [ ] 岗位详情页 Gap 列表展示

### Sprint 3: 成果流水线（第 5-6 周）

**目标**：用户可以提交成果，获得简历更新建议。

- [ ] 成果录入 API + UI
- [ ] Achievement Analysis Agent 节点
- [ ] Role Matching Agent 节点
- [ ] Resume Update Agent 节点
- [ ] 更新建议中心页面（列表 + 接受/拒绝）
- [ ] Gap Evaluation Agent 节点
- [ ] 成果确认后写入简历新版本

### Sprint 4: Gap 系统 + JD 定制（第 7-8 周）

**目标**：完整的 Gap 看板和 JD 定制流水线可用。

- [ ] Gap 看板页面（筛选、排序、详情抽屉）
- [ ] JD 输入 + JD Parsing Agent 节点
- [ ] JD Tailoring Agent 节点（双模式）
- [ ] 匹配评分逻辑
- [ ] JD 定制页面（完整步骤流程）
- [ ] 投递建议输出

### Sprint 5: 打磨 + 开源就绪（第 9-10 周）

**目标**：达到生产级质量，文档完善，可以对外开源。

- [ ] 版本历史 + Diff 对比
- [ ] Explain Agent 集成
- [ ] 完善双语文档
- [ ] API 文档（OpenAPI/Swagger）
- [ ] 测试覆盖率提升
- [ ] Docker 生产环境配置
- [ ] 性能审查和优化

---

## 参与贡献

我们欢迎各种形式的贡献！无论是 Bug 报告、功能建议、代码贡献还是文档改进。

请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解详细的贡献指南，包括：

- 开发环境搭建
- 代码规范和提交信息格式
- PR 提交流程
- Issue 报告模板

**快速开始贡献：**

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add some feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

如果你发现了 Bug 或有功能建议，欢迎提交 [Issue](https://github.com/your-username/CareerAgent/issues)。

---

## 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。

```
MIT License

Copyright (c) 2026 CareerAgent Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 致谢

CareerAgent 的构建离不开以下优秀的开源项目和技术：

- [FastAPI](https://fastapi.tiangolo.com/) -- 高性能异步 Python Web 框架
- [LangGraph](https://github.com/langchain-ai/langgraph) -- LLM 工作流编排框架
- [React](https://react.dev/) -- 用户界面构建库
- [Shadcn UI](https://ui.shadcn.com/) -- 高质量可复用 UI 组件
- [SQLAlchemy](https://www.sqlalchemy.org/) -- Python SQL 工具包和 ORM
- [Tailwind CSS](https://tailwindcss.com/) -- 实用优先的 CSS 框架
- [TanStack Query](https://tanstack.com/query/) -- 强大的异步状态管理
- [OpenAI](https://openai.com/) / [Anthropic](https://www.anthropic.com/) / [Google Gemini](https://ai.google.dev/) -- LLM 模型提供商

感谢所有为这个项目做出贡献的开发者。

---

<div align="center">

**如果这个项目对你有帮助，欢迎给个 Star 支持一下**

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/CareerAgent&type=Date)](https://star-history.com/#your-username/CareerAgent&Date)

</div>
