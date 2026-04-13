"""Import all ORM models so that Alembic can auto-detect them.

Every concrete model class must be imported here.  When new models are
added, add the corresponding import line below.
"""

from src.models.achievement import Achievement, AchievementResumeLink, AchievementRoleMatch
from src.models.agent import AgentRun, UpdateSuggestion
from src.models.gap import GapItem
from src.models.jd import JDResumeTask, JDSnapshot
from src.models.profile import CandidateProfile
from src.models.resume import Resume, ResumeVersion
from src.models.skill import SkillEntity
from src.models.target_role import RoleCapabilityModel, TargetRole
from src.models.user import User
from src.models.workspace import Workspace, WorkspaceMember

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
    "CandidateProfile",
]
