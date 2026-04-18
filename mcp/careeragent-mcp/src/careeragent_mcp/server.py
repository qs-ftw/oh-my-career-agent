"""CareerAgent MCP Server — exposes CareerAgent REST API as MCP tools."""

import json

from mcp.server.fastmcp import FastMCP

from .client import CareerAgentClient

mcp = FastMCP("CareerAgent")
_client = CareerAgentClient()


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


@mcp.tool()
async def career_get_achievement(achievement_id: str) -> str:
    """Get a single achievement's full details.

    Args:
        achievement_id: UUID of the achievement.
    """
    result = await _client.get(f"/achievements/{achievement_id}")
    return json.dumps(result, ensure_ascii=False, indent=2)


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


# --- Role tools ---


@mcp.tool()
async def career_list_roles() -> str:
    """List all target roles from CareerAgent."""
    resp = await _client.get("/roles")
    # Roles API returns {"items": [...], "total": N}
    results = resp.get("items", resp) if isinstance(resp, dict) else resp
    if not results:
        return "No target roles configured. Create roles in the CareerAgent web UI first."

    lines = []
    for r in results:
        name = r.get("role_name", r.get("title", r.get("name", "Unknown")))
        lines.append(f"- {r['id']}: {name}")
    return "\n".join(lines)


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


if __name__ == "__main__":
    mcp.run()
