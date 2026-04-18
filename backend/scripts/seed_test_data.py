"""Seed realistic test data for CareerAgent — roles + achievements + analysis."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.core.database import AsyncSessionLocal
from src.models.achievement import Achievement
from src.models.target_role import TargetRole
from src.models.resume import Resume, ResumeVersion
from src.models.gap import GapItem

USER_ID = "00000000-0000-0000-0000-000000000001"
WORKSPACE_ID = "00000000-0000-0000-0000-000000000001"

# ── Target Roles ──────────────────────────────────────────

ROLES = [
    {
        "role_name": "高级后端工程师",
        "role_type": "backend",
        "description": "负责核心业务系统架构设计和开发，要求精通 Python/Go，熟悉微服务架构，有高并发系统经验",
        "required_skills_json": ["Python", "Go", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes", "微服务架构"],
        "bonus_skills_json": ["CI/CD", "系统设计", "团队管理", "开源贡献"],
        "keywords_json": ["后端", "微服务", "高并发", "分布式", "云原生"],
        "priority": 10,
    },
    {
        "role_name": "全栈工程师",
        "role_type": "fullstack",
        "description": "负责产品从0到1的全栈开发，前端 React + 后端 Python，要求有独立交付能力",
        "required_skills_json": ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker"],
        "bonus_skills_json": ["Next.js", "Tailwind CSS", "Vercel", "产品思维"],
        "keywords_json": ["全栈", "React", "独立交付", "SaaS"],
        "priority": 8,
    },
    {
        "role_name": "AI 应用工程师",
        "role_type": "ai_engineer",
        "description": "负责 AI 产品的工程化落地，包括 LLM 应用开发、RAG 系统、Agent 编排",
        "required_skills_json": ["Python", "LangChain", "LLM", "RAG", "向量数据库", "Prompt Engineering"],
        "bonus_skills_json": ["LangGraph", "Agent 框架", "模型微调", "MLOps"],
        "keywords_json": ["AI", "LLM", "RAG", "Agent", "工程化"],
        "priority": 9,
    },
]

# ── Achievements ──────────────────────────────────────────

ACHIEVEMENTS = [
    {
        "title": "重构核心交易系统为微服务架构",
        "raw_content": (
            "主导将公司核心交易系统从单体架构迁移到微服务架构。使用 Python/FastAPI 重写订单服务、支付服务、库存服务，"
            "引入 PostgreSQL 作为主存储，Redis 做缓存和分布式锁。通过服务拆分和异步化改造，API 平均响应时间从 800ms 降低到 120ms，"
            "系统吞吐量提升 5 倍。使用 Docker + Kubernetes 部署，实现零停机发布。管理 4 人后端团队，制定代码规范和 CR 流程。"
        ),
        "tags": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes", "微服务"],
        "summary": "主导核心交易系统微服务化，API 响应时间降低 85%，吞吐量提升 5 倍",
        "metrics": [
            {"description": "API 响应时间优化", "value": "800ms → 120ms"},
            {"description": "系统吞吐量提升", "value": "5x"},
            {"description": "团队规模", "value": "4人"},
        ],
    },
    {
        "title": "搭建实时数据监控平台",
        "raw_content": (
            "从零搭建面向业务方的实时数据监控平台。前端使用 React + TypeScript + ECharts，"
            "后端使用 Python + WebSocket 推送实时指标。支持自定义看板、告警规则配置、多维度下钻分析。"
            "接入 50+ 业务指标数据源，日活用户 200+，帮助运营团队将问题发现时间从小时级缩短到分钟级。"
        ),
        "tags": ["React", "TypeScript", "Python", "WebSocket", "ECharts"],
        "summary": "从零搭建实时监控平台，接入 50+ 数据源，日活 200+",
        "metrics": [
            {"description": "数据源接入", "value": "50+"},
            {"description": "日活用户", "value": "200+"},
            {"description": "问题发现时间缩短", "value": "小时级 → 分钟级"},
        ],
    },
    {
        "title": "构建 LLM 驱动的智能客服系统",
        "raw_content": (
            "设计并实现基于大语言模型的智能客服系统。使用 LangChain 编排多轮对话 Agent，结合 RAG 检索企业知识库，"
            "实现意图识别、多轮澄清、知识问答、工单创建等能力。采用 Milvus 做向量检索，PostgreSQL 存储对话历史。"
            "上线后自动解决率达到 72%，人工客服工作量减少 40%。"
        ),
        "tags": ["LangChain", "LLM", "RAG", "Milvus", "Python", "PostgreSQL", "Agent"],
        "summary": "构建 LLM 智能客服系统，自动解决率 72%，减少 40% 人工工作量",
        "metrics": [
            {"description": "自动解决率", "value": "72%"},
            {"description": "人工工作量减少", "value": "40%"},
            {"description": "平均响应时间", "value": "1.5s"},
        ],
    },
    {
        "title": "开发开源 API 网关项目",
        "raw_content": (
            "独立开发并开源了一个轻量级 API 网关，使用 Go 语言实现，支持限流、熔断、负载均衡、JWT 鉴权等核心功能。"
            "采用插件化架构，方便扩展。在 GitHub 获得 1.2k stars，被 3 家公司采用。写了完整的技术文档和 30+ 单元测试。"
        ),
        "tags": ["Go", "开源", "API 网关", "系统设计", "插件化架构"],
        "summary": "开源 Go API 网关，GitHub 1.2k stars，被 3 家公司生产使用",
        "metrics": [
            {"description": "GitHub Stars", "value": "1.2k"},
            {"description": "采用公司", "value": "3家"},
            {"description": "单元测试覆盖", "value": "30+ 用例"},
        ],
    },
    {
        "title": "优化前端构建性能",
        "raw_content": (
            "负责优化一个大型 React 项目的前端构建性能。项目使用 TypeScript + Vite + Tailwind CSS，"
            "随着业务增长构建时间从 30s 增长到 3min。通过代码分割、Tree Shaking 优化、DLL 预编译、"
            "CI 缓存策略等手段，将构建时间压缩到 45s。首屏加载时间从 4.2s 降低到 1.8s，LCP 优化 57%。"
        ),
        "tags": ["React", "TypeScript", "Vite", "Tailwind CSS", "性能优化"],
        "summary": "优化前端构建性能，构建时间 3min → 45s，首屏 LCP 优化 57%",
        "metrics": [
            {"description": "构建时间优化", "value": "3min → 45s"},
            {"description": "首屏加载时间", "value": "4.2s → 1.8s"},
            {"description": "LCP 优化", "value": "57%"},
        ],
    },
    {
        "title": "设计并实现自动化 CI/CD 流水线",
        "raw_content": (
            "为 20+ 微服务项目设计统一的 CI/CD 流水线。使用 GitHub Actions + Docker + ArgoCD 实现 GitOps 工作流。"
            "支持自动构建、单元测试、集成测试、安全扫描、灰度发布、回滚。将发布频率从每周一次提升到每天多次，"
            "发布时间从 2 小时缩短到 15 分钟。"
        ),
        "tags": ["CI/CD", "GitHub Actions", "Docker", "ArgoCD", "GitOps", "Kubernetes"],
        "summary": "设计 GitOps CI/CD 流水线，发布频率周级 → 日级，发布时间 2h → 15min",
        "metrics": [
            {"description": "覆盖服务数", "value": "20+"},
            {"description": "发布时间缩短", "value": "2h → 15min"},
            {"description": "发布频率提升", "value": "周级 → 日级多次"},
        ],
    },
]


async def seed():
    async with AsyncSessionLocal() as session:
        # 1. Create target roles
        print("Creating target roles...")
        for r in ROLES:
            role = TargetRole(
                workspace_id=WORKSPACE_ID,
                user_id=USER_ID,
                **r,
                status="active",
            )
            session.add(role)
        await session.flush()

        # 2. Create achievements with parsed data
        print("Creating achievements...")
        for a in ACHIEVEMENTS:
            ach = Achievement(
                workspace_id=WORKSPACE_ID,
                user_id=USER_ID,
                source_type="manual",
                title=a["title"],
                raw_content=a["raw_content"],
                parsed_summary=a["summary"],
                tags_json=a["tags"],
                metrics_json=a.get("metrics", []),
                importance_score=0.7,
            )
            session.add(ach)

        await session.flush()
        await session.commit()
        print(f"Seeded {len(ROLES)} roles + {len(ACHIEVEMENTS)} achievements")


if __name__ == "__main__":
    asyncio.run(seed())
