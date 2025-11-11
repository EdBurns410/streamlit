import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


class ToolStatus(enum.Enum):
    IDLE = "idle"
    BUILDING = "building"
    RUNNING = "running"
    ERROR = "error"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tools = relationship("Tool", back_populates="owner", lazy="selectin")


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ToolStatus), default=ToolStatus.IDLE, nullable=False)
    current_image_ref = Column(String(512), nullable=True)
    current_version_id = Column(Integer, ForeignKey("tool_versions.id"), nullable=True)

    owner = relationship("User", back_populates="tools", lazy="joined")
    versions = relationship("ToolVersion", back_populates="tool", cascade="all, delete", lazy="selectin")
    runs = relationship("ToolRun", back_populates="tool", cascade="all, delete", lazy="selectin")


class ToolVersion(Base):
    __tablename__ = "tool_versions"

    id = Column(Integer, primary_key=True, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    app_py = Column(Text, nullable=False)
    requirements_txt = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata = Column(JSONB, nullable=True)

    tool = relationship("Tool", back_populates="versions", lazy="joined")
    builds = relationship("ToolBuild", back_populates="version", cascade="all, delete", lazy="selectin")


class BuildStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ToolBuild(Base):
    __tablename__ = "tool_builds"

    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("tool_versions.id"), nullable=False)
    status = Column(Enum(BuildStatus), default=BuildStatus.PENDING, nullable=False)
    logs = Column(Text, nullable=True)
    image_ref = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    version = relationship("ToolVersion", back_populates="builds")


class RunStatus(enum.Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class ToolRun(Base):
    __tablename__ = "tool_runs"

    id = Column(Integer, primary_key=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False)
    build_id = Column(Integer, ForeignKey("tool_builds.id"), nullable=False)
    status = Column(Enum(RunStatus), default=RunStatus.STARTING, nullable=False)
    container_id = Column(String(255), nullable=True)
    url = Column(String(512), nullable=True)
    logs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tool = relationship("Tool", back_populates="runs", lazy="joined")
