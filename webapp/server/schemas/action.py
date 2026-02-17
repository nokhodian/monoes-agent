from pydantic import BaseModel, Field
from typing import List, Optional, Literal

ActionType = Literal["BULK_MESSAGING", "KEYWORD_SEARCH", "PUBLISH_CONTENT", "PROFILE_INTERACTION"]
ActionState = Literal["PENDING", "INPROGRESS", "PAUSE", "DONE"]
Platform = Literal["TELEGRAM", "X", "INSTAGRAM", "LINKEDIN", "EMAIL", "TIKTOK"]
SourceType = Literal["LIKE", "COMMENT", "MESSAGE", "PROFILE", "SEARCH"]

class ActionTargetDTO(BaseModel):
    id: str
    actionId: str
    personId: str
    platform: Platform
    link: str
    sourceType: SourceType
    status: Literal["PENDING", "INPROGRESS", "DONE", "FAILED"]
    lastInteractedAt: Optional[str] = None
    commentText: Optional[str] = None
    metadata: Optional[dict] = None

class ActionDTO(BaseModel):
    id: str
    createdAt: int
    createdBy: str
    ownerId: str
    title: str
    type: ActionType
    state: ActionState
    disabled: bool = False
    targetPlatform: Platform
    position: int = 0
    cost: int = 0
    actionExecutionCount: int = 0
    contentSubject: Optional[str] = None
    contentMessage: Optional[str] = None
    contentBlobURL: List[str] = Field(default_factory=list)
    scheduledDate: Optional[str] = None
    executionInterval: int = 0
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    campaignID: Optional[str] = None
    actionTarget: Optional[List[ActionTargetDTO]] = None

class CreateActionDTO(BaseModel):
    createdBy: str
    ownerId: str
    title: str
    type: ActionType
    state: ActionState = "PENDING"
    targetPlatform: Platform
    contentSubject: Optional[str] = None
    contentMessage: Optional[str] = None
    contentBlobURL: List[str] = Field(default_factory=list)
    scheduledDate: Optional[str] = None
    executionInterval: int = 0
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    campaignID: Optional[str] = None

class PatchActionDTO(BaseModel):
    title: Optional[str] = None
    state: Optional[ActionState] = None
    disabled: Optional[bool] = None
    position: Optional[int] = None
    cost: Optional[int] = None
    actionExecutionCount: Optional[int] = None
    contentSubject: Optional[str] = None
    contentMessage: Optional[str] = None
    contentBlobURL: Optional[List[str]] = None
    scheduledDate: Optional[str] = None
    executionInterval: Optional[int] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    campaignID: Optional[str] = None

class PatchStateDTO(BaseModel):
    state: ActionState
