from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from .models import BuildStatus, RunStatus, ToolStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


class ToolBase(BaseModel):
    name: str
    description: Optional[str] = None


class ToolCreate(ToolBase):
    pass


class ToolOut(ToolBase):
    id: int
    owner_id: int
    status: ToolStatus
    current_image_ref: Optional[str]

    class Config:
        orm_mode = True


class VersionUpload(BaseModel):
    app_py: str
    requirements_txt: str


class BuildOut(BaseModel):
    id: int
    status: BuildStatus
    logs: Optional[str]
    image_ref: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class ToolVersionOut(BaseModel):
    id: int
    tool_id: int
    created_at: datetime
    builds: List[BuildOut] = []

    class Config:
        orm_mode = True


class RunOut(BaseModel):
    id: int
    status: RunStatus
    url: Optional[str]
    logs: Optional[str]

    class Config:
        orm_mode = True


class ToolDetail(ToolOut):
    versions: List[ToolVersionOut] = []
    runs: List[RunOut] = []


class BuildRequest(BaseModel):
    version_id: Optional[int] = None
