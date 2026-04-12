"""Prompt template for the Gap Evaluation agent node."""

GAP_EVALUATION_PROMPT: str = """\
You are evaluating skill gaps between a software engineer's profile and a target role.

## Input
Achievement:
{achievement_parsed}

Current gaps for role:
{current_gaps}

Target role capability model:
{capability_model}

## Task
Determine whether this achievement affects any existing gaps:
- If a gap is now partially or fully addressed, update its progress and evidence.
- If a new gap area is revealed, create a new gap entry.
- Provide improvement plan suggestions for any remaining gaps.

## Output Format
Return a JSON array of gap update objects matching the GapUpdate schema.
"""
