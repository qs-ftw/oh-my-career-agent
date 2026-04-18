"""Resume PDF import service — extract text and parse structured info via LLM.

Supports deduplication: if a company or project semantically matches an existing
entity, it updates instead of creating a duplicate.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import uuid

import pdfplumber
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.achievement import Achievement
from src.models.education import Education
from src.models.profile import CareerProfile
from src.models.project import Project
from src.models.work_experience import WorkExperience
from src.schemas.profile import CareerProfileUpsert
from src.schemas.work_experience import WorkExperienceCreate
from src.schemas.project import ProjectCreate
from src.schemas.achievement import AchievementCreate
from src.schemas.education import EducationCreate

logger = logging.getLogger(__name__)

_LLM_TIMEOUT = 120

_PARSE_PROMPT = """\
你是一位简历信息提取专家。请从以下简历文本中提取结构化信息。

简历文本：
---
{resume_text}
---

返回JSON对象（严格按此格式）：
{{
  "profile": {{
    "name": "姓名",
    "headline": "职业标语，如：高级后端工程师 | 8年分布式系统经验",
    "email": "邮箱",
    "phone": "电话",
    "linkedin_url": "LinkedIn URL或空字符串",
    "github_url": "GitHub URL或空字符串",
    "portfolio_url": "作品集URL或空字符串",
    "location": "所在城市",
    "professional_summary": "专业摘要，2-3句话概括核心优势"
  }},
  "skill_categories": {{
    "编程语言": ["Python", "Go"],
    "框架与中间件": ["FastAPI", "Kafka"],
    "基础设施": ["Kubernetes", "AWS"],
    "数据库": ["PostgreSQL", "Redis"]
  }},
  "work_experiences": [
    {{
      "company_name": "公司名",
      "company_url": "公司URL或空字符串",
      "location": "工作城市",
      "role_title": "职位名称",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD 或 null(表示至今)",
      "description": "工作职责描述，用分号分隔要点"
    }}
  ],
  "educations": [
    {{
      "institution_name": "学校名称",
      "institution_url": "",
      "degree": "学位如本科/硕士/博士",
      "field_of_study": "专业名称",
      "location": "城市",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD or null",
      "gpa": "GPA或空字符串",
      "description": "在校活动、荣誉奖项"
    }}
  ],
  "projects": [
    {{
      "name": "项目名",
      "description": "项目描述，包括背景、技术方案和关键成果",
      "tech_stack": ["技术1", "技术2"],
      "url": "项目URL或空字符串",
      "start_date": "YYYY-MM-DD 或 null",
      "end_date": "YYYY-MM-DD 或 null",
      "company_name": "所属公司名(用于关联到work_experience)或空字符串(表示独立项目)"
    }}
  ],
  "achievements": [
    {{
      "title": "成果标题，简洁有力，如：DAU提升23%的用户增长实验体系",
      "raw_content": "成果的详细描述，包含背景、行动、结果(STAR格式)",
      "tags": ["标签1", "标签2"],
      "company_name": "所属公司名(用于关联)",
      "project_name": "所属项目名(用于关联)或空字符串"
    }}
  ]
}}

规则：
- 日期格式必须是 YYYY-MM-DD，如果只有年月则用 YYYY-MM-01
- 如果至今在职，end_date 设为 null
- professional_summary 要精炼，突出核心竞争力
- 技能分类要准确，每个分类下放3-8个技能
- 项目描述要包含背景、技术方案和量化成果
- 每个项目下提取2-5个关键成果作为achievements
- 成果标题要突出价值，如"XX提升YY%"而不是简单的"做了XX"
- 成果的raw_content用STAR格式描述：情境、任务、行动、结果
- 绝不编造信息，只提取简历中明确提到的内容
- 如果某个字段信息缺失，用空字符串或空数组
- 只返回JSON，不要其他文字"""

_DEDUP_PROMPT = """\
你是一位数据匹配专家。判断两组数据是否代表同一个实体。

已有数据：
{existing_json}

新提取数据：
{new_json}

对每个新提取的条目，判断它是否与已有条目中的某一条匹配（语义相同，非字面匹配）。

返回JSON数组：
[
  {{
    "new_index": 0,
    "matches_existing": true,
    "existing_index": 2,
    "confidence": 0.95,
    "reason": "都是字节跳动的高级后端工程师职位"
  }}
]

规则：
- 公司名称的简称/全称/英文/中文都算匹配（如"字节跳动"="ByteDance"）
- 同一家公司不同时期的不同职位不算匹配
- 项目名语义相同就匹配（如"用户增长平台"="用户画像与增长平台"）
- confidence >= 0.7 才算匹配
- 只返回JSON数组，不要其他文字"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text content from a PDF file."""
    try:
        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.warning(f"PDF text extraction failed: {e}")
        raise ValueError(f"无法解析PDF文件: {e}")


async def _parse_resume_with_llm(resume_text: str) -> dict:
    """Use LLM to parse structured info from resume text."""
    user_prompt = _PARSE_PROMPT.format(resume_text=resume_text[:8000])

    try:
        from src.core.llm import get_llm

        llm = get_llm("resume_import")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": "你是简历信息提取专家。只返回JSON。"},
                {"role": "user", "content": user_prompt},
            ]),
            timeout=_LLM_TIMEOUT,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except asyncio.TimeoutError:
        logger.warning("[resume_import] LLM timed out")
        raise
    except json.JSONDecodeError as e:
        logger.warning(f"[resume_import] LLM returned invalid JSON: {e}")
        raise
    except Exception as e:
        logger.warning(f"[resume_import] LLM parsing failed: {e}")
        raise


async def _dedup_with_llm(
    existing_items: list[dict],
    new_items: list[dict],
    item_type: str,
) -> list[dict]:
    """Use LLM to semantically match new items against existing ones.

    Returns a list of match dicts: [{new_index, matches_existing, existing_index}, ...]
    """
    if not existing_items or not new_items:
        return []

    prompt = _DEDUP_PROMPT.format(
        existing_json=json.dumps(existing_items, ensure_ascii=False, indent=2),
        new_json=json.dumps(new_items, ensure_ascii=False, indent=2),
    )

    try:
        from src.core.llm import get_llm

        llm = get_llm("resume_import")
        response = await asyncio.wait_for(
            llm.ainvoke([
                {"role": "system", "content": f"你是数据匹配专家。判断{item_type}是否匹配。只返回JSON。"},
                {"role": "user", "content": prompt},
            ]),
            timeout=60,
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[resume_import] Dedup LLM failed for {item_type}: {e}")
        return []


async def _load_existing_wes(session: AsyncSession, profile_id: uuid.UUID) -> list[WorkExperience]:
    stmt = select(WorkExperience).where(WorkExperience.profile_id == profile_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _load_existing_projects(session: AsyncSession, profile_id: uuid.UUID) -> list[Project]:
    stmt = select(Project).where(Project.profile_id == profile_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _parse_date(date_str: str | None) -> object:
    """Parse a date string, returning date or None."""
    from datetime import date as date_type
    if not date_str or (isinstance(date_str, str) and date_str.lower() == "null"):
        return None
    try:
        return date_type.fromisoformat(str(date_str))
    except (ValueError, TypeError):
        return None


async def import_resume_pdf(
    session: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    file_bytes: bytes,
) -> dict:
    """Import a resume PDF: extract text, parse via LLM, dedup, and persist data.

    Deduplication: uses LLM-based semantic matching to identify existing companies
    and projects, updating them instead of creating duplicates.

    Returns a dict with:
      - profile: updated profile data
      - work_experiences: list of {id, company_name, role_title, action}
      - projects: list of {id, name, company_name, action}
      - achievements: list of {id, title, action}
    """
    # 1. Extract text from PDF
    resume_text = extract_text_from_pdf(file_bytes)
    if not resume_text.strip():
        raise ValueError("无法从PDF中提取文本，请确认文件内容")

    # 2. Parse via LLM
    parsed = await _parse_resume_with_llm(resume_text)

    # 3. Upsert profile
    profile_data = parsed.get("profile", {})
    skill_categories = parsed.get("skill_categories", {})

    from src.services.profile_service import upsert_profile

    profile_upsert = CareerProfileUpsert(
        name=profile_data.get("name", ""),
        headline=profile_data.get("headline", ""),
        email=profile_data.get("email", ""),
        phone=profile_data.get("phone", ""),
        linkedin_url=profile_data.get("linkedin_url", ""),
        portfolio_url=profile_data.get("portfolio_url", ""),
        github_url=profile_data.get("github_url", ""),
        location=profile_data.get("location", ""),
        professional_summary=profile_data.get("professional_summary", ""),
        skill_categories=skill_categories,
    )
    profile_resp = await upsert_profile(session, user_id, workspace_id, profile_upsert)
    profile_id = profile_resp.id

    # 4. Load existing data for dedup
    existing_wes = await _load_existing_wes(session, profile_id)
    existing_projects = await _load_existing_projects(session, profile_id)

    existing_we_summaries = [
        {"index": i, "company_name": we.company_name, "role_title": we.role_title}
        for i, we in enumerate(existing_wes)
    ]
    existing_proj_summaries = [
        {"index": i, "name": p.name, "company_name": ""}
        for i, p in enumerate(existing_projects)
    ]
    # Enrich project summaries with company name
    we_by_id = {we.id: we for we in existing_wes}
    for i, p in enumerate(existing_projects):
        if p.work_experience_id and p.work_experience_id in we_by_id:
            existing_proj_summaries[i]["company_name"] = we_by_id[p.work_experience_id].company_name

    new_we_data = parsed.get("work_experiences", [])
    new_proj_data = parsed.get("projects", [])

    # 5. Dedup work experiences via LLM
    we_matches = await _dedup_with_llm(existing_we_summaries, new_we_data, "工作经历")

    we_map: dict[str, uuid.UUID] = {}  # company_name -> we_id
    created_wes: list[dict] = []

    from src.services.work_experience_service import create as create_we, update as update_we
    from src.schemas.work_experience import WorkExperienceUpdate

    match_by_new_idx = {m["new_index"]: m for m in we_matches}

    for i, we_data in enumerate(new_we_data):
        start_date = _parse_date(we_data.get("start_date"))
        end_date = _parse_date(we_data.get("end_date"))

        match = match_by_new_idx.get(i)
        if match and match.get("matches_existing") and match.get("confidence", 0) >= 0.7:
            # Update existing WE
            existing_idx = match["existing_index"]
            existing_we = existing_wes[existing_idx]
            update_data = WorkExperienceUpdate(
                company_name=we_data.get("company_name") or existing_we.company_name,
                role_title=we_data.get("role_title") or existing_we.role_title,
                location=we_data.get("location") or existing_we.location,
                description=we_data.get("description") or existing_we.description,
            )
            if start_date:
                update_data.start_date = start_date
            if end_date:
                update_data.end_date = end_date
            await update_we(session, existing_we.id, update_data)
            we_map[we_data.get("company_name", "").strip()] = existing_we.id
            created_wes.append({
                "id": str(existing_we.id),
                "company_name": existing_we.company_name,
                "role_title": existing_we.role_title,
                "action": "updated",
            })
        else:
            # Create new WE
            we_create = WorkExperienceCreate(
                company_name=we_data.get("company_name", ""),
                company_url=we_data.get("company_url", ""),
                location=we_data.get("location", ""),
                role_title=we_data.get("role_title", ""),
                start_date=start_date,
                end_date=end_date,
                description=we_data.get("description", ""),
                sort_order=i,
            )
            we_resp = await create_we(session, profile_id, we_create)
            we_map[we_data.get("company_name", "").strip()] = we_resp.id
            created_wes.append({
                "id": str(we_resp.id),
                "company_name": we_resp.company_name,
                "role_title": we_resp.role_title,
                "action": "created",
            })

    # 6. Dedup projects via LLM
    proj_matches = await _dedup_with_llm(existing_proj_summaries, new_proj_data, "项目")

    proj_map: dict[str, uuid.UUID] = {}  # "company_name|project_name" -> project_id
    created_projects: list[dict] = []

    from src.services.project_service import create as create_project, update as update_project
    from src.schemas.project import ProjectUpdate

    proj_match_by_new_idx = {m["new_index"]: m for m in proj_matches}

    for i, proj_data in enumerate(new_proj_data):
        company_name = proj_data.get("company_name", "").strip()
        we_id = we_map.get(company_name)
        start_date = _parse_date(proj_data.get("start_date"))
        end_date = _parse_date(proj_data.get("end_date"))

        match = proj_match_by_new_idx.get(i)
        if match and match.get("matches_existing") and match.get("confidence", 0) >= 0.7:
            # Update existing project
            existing_idx = match["existing_index"]
            existing_proj = existing_projects[existing_idx]
            update_data = ProjectUpdate(
                description=proj_data.get("description") or existing_proj.description,
                tech_stack=proj_data.get("tech_stack") or existing_proj.tech_stack,
            )
            if start_date:
                update_data.start_date = start_date
            if end_date:
                update_data.end_date = end_date
            if we_id:
                update_data.work_experience_id = we_id
            await update_project(session, existing_proj.id, update_data)
            proj_map[f"{company_name}|{proj_data.get('name', '')}"] = existing_proj.id
            created_projects.append({
                "id": str(existing_proj.id),
                "name": existing_proj.name,
                "company_name": company_name or None,
                "action": "updated",
            })
        else:
            # Create new project
            proj_create = ProjectCreate(
                work_experience_id=we_id,
                name=proj_data.get("name", ""),
                description=proj_data.get("description", ""),
                tech_stack=proj_data.get("tech_stack", []),
                url=proj_data.get("url", ""),
                start_date=start_date,
                end_date=end_date,
                sort_order=i,
            )
            proj_resp = await create_project(session, profile_id, proj_create)
            proj_map[f"{company_name}|{proj_data.get('name', '')}"] = proj_resp.id
            created_projects.append({
                "id": str(proj_resp.id),
                "name": proj_resp.name,
                "company_name": company_name or None,
                "action": "created",
            })

    # 7. Create achievements
    created_achievements: list[dict] = []

    from src.services.achievement_service import create_achievement

    for ach_data in parsed.get("achievements", []):
        company_name = ach_data.get("company_name", "").strip()
        project_name = ach_data.get("project_name", "").strip()

        # Resolve project_id and work_experience_id
        project_id = None
        work_experience_id = we_map.get(company_name)
        if company_name and project_name:
            project_id = proj_map.get(f"{company_name}|{project_name}")
        if not project_id and project_name:
            # Try matching by project name alone
            for key, pid in proj_map.items():
                if key.endswith(f"|{project_name}"):
                    project_id = pid
                    break

        ach_create = AchievementCreate(
            title=ach_data.get("title", ""),
            raw_content=ach_data.get("raw_content", ""),
            tags=ach_data.get("tags", []),
            project_id=project_id,
            work_experience_id=work_experience_id,
            source_type="resume_import",
        )
        ach_resp = await create_achievement(session, user_id, workspace_id, ach_create)
        created_achievements.append({
            "id": str(ach_resp.id),
            "title": ach_resp.title,
            "action": "created",
        })

    # 8. Create education records
    created_educations: list[dict] = []
    from src.services.education_service import create as create_edu

    for i, edu_data in enumerate(parsed.get("educations", [])):
        start_date = _parse_date(edu_data.get("start_date"))
        end_date = _parse_date(edu_data.get("end_date"))
        if not start_date:
            continue

        edu_create = EducationCreate(
            institution_name=edu_data.get("institution_name", ""),
            institution_url=edu_data.get("institution_url", ""),
            degree=edu_data.get("degree", ""),
            field_of_study=edu_data.get("field_of_study", ""),
            location=edu_data.get("location", ""),
            start_date=start_date,
            end_date=end_date,
            gpa=edu_data.get("gpa", ""),
            description=edu_data.get("description", ""),
            sort_order=i,
        )
        edu_resp = await create_edu(session, profile_id, edu_create)
        created_educations.append({
            "id": str(edu_resp.id),
            "institution_name": edu_resp.institution_name,
            "action": "created",
        })

    await session.commit()

    return {
        "profile": profile_resp.model_dump(),
        "work_experiences": created_wes,
        "projects": created_projects,
        "achievements": created_achievements,
        "educations": created_educations,
    }
