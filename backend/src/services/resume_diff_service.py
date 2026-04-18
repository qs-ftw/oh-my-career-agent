"""Pure helper for comparing two ResumeContent payloads."""

from __future__ import annotations

from typing import Any


def summarize_resume_diff(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare two resume content dicts and emit a section-level diff summary.

    Returns a dict with:
      - summary_changed: bool
      - section_counts: per-section add/remove counts
      - notable_updates: list of notable changes
    """
    sections = ["summary", "skills", "experiences", "projects", "highlights", "metrics", "interview_points"]
    section_counts: dict[str, dict[str, int]] = {}
    notable_updates: list[str] = []

    for section in sections:
        prev_val = previous.get(section) or []
        curr_val = current.get(section) or []

        if section == "summary":
            changed = str(prev_val) != str(curr_val)
            section_counts[section] = {"changed": 1 if changed else 0}
            if changed and curr_val:
                notable_updates.append(f"摘要已更新")
        elif isinstance(prev_val, list) and isinstance(curr_val, list):
            prev_len = len(prev_val)
            curr_len = len(curr_val)
            added = max(0, curr_len - prev_len)
            removed = max(0, prev_len - curr_len)
            section_counts[section] = {"added": added, "removed": removed, "total": curr_len}
            if added > 0:
                notable_updates.append(f"{section} 新增 {added} 项")
            if removed > 0:
                notable_updates.append(f"{section} 移除 {removed} 项")

    return {
        "summary_changed": str(previous.get("summary")) != str(current.get("summary")),
        "section_counts": section_counts,
        "notable_updates": notable_updates,
    }
