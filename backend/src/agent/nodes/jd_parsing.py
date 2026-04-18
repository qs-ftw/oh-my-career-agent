"""JD Parsing node — extracts structured data from raw JD text."""

from __future__ import annotations

import json
import logging
import re

from src.agent.state import CareerAgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an expert job description parser for software engineering roles.

Given the raw job description text, extract structured information as JSON:
{
  "role_name": "Position title",
  "keywords": ["list of important keywords and phrases"],
  "required_skills": ["list of required technical skills and technologies"],
  "bonus_items": ["list of nice-to-have skills and qualifications"],
  "style": {
    "tone": "formal|casual|technical",
    "length": "brief|medium|detailed",
    "focus": "engineering|algorithm|business|leadership",
    "experience_level": "junior|mid|senior|staff|principal"
  }
}

Be thorough in skill extraction. Include both explicit and implicit requirements.
Return ONLY the JSON object, no other text.
"""


async def jd_parsing(state: CareerAgentState) -> dict:
    """Parse raw JD text into a structured JD object.

    Uses LLM if available, otherwise falls back to keyword extraction.
    """
    jd_raw = state.get("jd_raw", "")

    user_prompt = f"Parse this job description:\n\n{jd_raw}"

    # Try LLM-based parsing
    parsed = None
    try:
        from src.core.llm import get_llm

        llm = get_llm("jd_parsing")
        response = await llm.ainvoke(
            [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
        )
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())
    except Exception as e:
        logger.info(f"LLM JD parsing failed ({e}), using template fallback")

    # Fallback: basic keyword extraction
    if not parsed:
        raw_lower = jd_raw.lower()

        # Extract common tech skills
        tech_keywords = [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
            "react", "vue", "angular", "node", "next.js", "svelte",
            "fastapi", "django", "flask", "spring", "express",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "terraform", "aws", "gcp", "azure",
            "kafka", "rabbitmq", "grpc", "graphql", "rest",
            "ci/cd", "git", "linux", "microservice", "distributed",
            "machine learning", "deep learning", "nlp", "data pipeline",
        ]
        found_skills = [t for t in tech_keywords if t in raw_lower]

        # Try to extract role name from first line or common patterns
        role_name = ""
        lines = jd_raw.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            # Common JD title patterns
            for pattern in [
                r"(?:senior|junior|staff|principal|lead)?\s*(?:software|backend|frontend|full.?stack|data|ml|devops|platform|infrastructure)\s*(?:engineer|developer|architect|scientist)",
                r"(.{5,50})",
            ]:
                match = re.search(pattern, first_line, re.IGNORECASE)
                if match:
                    role_name = match.group(0).strip()
                    break

        parsed = {
            "role_name": role_name or "Software Engineer",
            "keywords": list(set(found_skills[:10])),
            "required_skills": found_skills[:8],
            "bonus_items": found_skills[8:12],
            "style": {
                "tone": "formal",
                "length": "medium",
                "focus": "engineering",
                "experience_level": "mid",
            },
        }

    return {
        "jd_parsed": parsed,
        "agent_logs": state.get("agent_logs", []) + [
            {
                "node": "jd_parsing",
                "action": "parsed_jd",
                "role_name": parsed.get("role_name", ""),
                "skills_count": len(parsed.get("required_skills", [])),
            }
        ],
    }
