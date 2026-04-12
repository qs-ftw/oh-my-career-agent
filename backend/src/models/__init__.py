"""Import all ORM models so that Alembic can auto-detect them.

Every concrete model class must be imported here.  When new models are
added, add the corresponding import line below.
"""

from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember
from src.models.target_role import TargetRole, RoleCapabilityModel
from src.models.resume import Resume, ResumeVersion
from src.models.achievement import Achievement, AchievementRoleMatch, AchievementResumeLink
from src.models.skill import SkillEntity
from src.models.gap import GapItem
from src.models.jd import JDSnapshot, JDResumeTask
from src.models.agent import AgentRun, UpdateSuggestion

__all__ = [
    "User",
    "Workspace",
    "WorkspaceMember",
    "TargetRole",
    "RoleCapabilityModel",
    "Resume",
    "ResumeVersion",
    "Achievement",
    "AchievementRoleMatch",
    "AchievementResumeLink",
    "SkillEntity",
    "GapItem",
    "JDSnapshot",
    "JDResumeTask",
    "AgentRun",
    "UpdateSuggestion",
]
