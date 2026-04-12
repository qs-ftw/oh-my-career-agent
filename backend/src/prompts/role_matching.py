"""Prompt template for the Role Matching agent node."""

ROLE_MATCHING_PROMPT: str = """\
You are matching a parsed achievement against active target roles.

## Input
Parsed achievement:
{achievement_parsed}

Target roles:
{target_roles}

## Task
For each role, compute a match relevance score (0.0-1.0) and a brief reason
explaining why the achievement is relevant (or not) to that role.

## Output Format
Return a JSON array of objects:
[{{"role_id": "...", "match_score": 0.0, "reason": "..."}}]
"""
