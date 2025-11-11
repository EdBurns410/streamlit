from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import auth
from .auth import create_access_token, get_password_hash, get_current_user
from .config import get_settings
from .database import Base, engine, get_session
from .models import Tool, ToolBuild, ToolStatus, ToolVersion, User
from .schemas import BuildRequest, ToolCreate, ToolDetail, ToolOut, UserCreate, UserOut
from .tasks import execute_build, execute_run, execute_stop
from .utils.packaging import PackagingError, load_version_payload

settings = get_settings()

app = FastAPI(title="Sheetify Studio API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.post("/v1/auth/register", response_model=UserOut)
async def register_user(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == payload.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, password_hash=get_password_hash(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@app.post("/v1/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    user = await auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/v1/tools", response_model=ToolOut)
async def create_tool(
    payload: ToolCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tool = Tool(name=payload.name, description=payload.description, owner_id=user.id)
    session.add(tool)
    await session.commit()
    await session.refresh(tool, attribute_names=["versions", "runs"])
    for version in tool.versions:
        await session.refresh(version, attribute_names=["builds"])
    return tool


@app.get("/v1/tools/{tool_id}", response_model=ToolDetail)
async def get_tool(tool_id: int, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)):
    result = await session.execute(select(Tool).where(Tool.id == tool_id, Tool.owner_id == user.id))
    tool = result.scalars().first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    await session.refresh(tool, attribute_names=["versions", "runs"])
    for version in tool.versions:
        await session.refresh(version, attribute_names=["builds"])
    return tool


@app.post("/v1/tools/{tool_id}/versions")
async def upload_version(
    tool_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tool = await session.get(Tool, tool_id)
    if not tool or tool.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    try:
        contents = await file.read()
        app_py, requirements_txt = load_version_payload(file.filename, contents)
    except PackagingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    version = ToolVersion(tool_id=tool_id, app_py=app_py, requirements_txt=requirements_txt)
    session.add(version)
    await session.commit()
    await session.refresh(version)
    return {"version_id": version.id}


@app.post("/v1/tools/{tool_id}/build")
async def build_tool(
    tool_id: int,
    payload: BuildRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tool = await session.get(Tool, tool_id)
    if not tool or tool.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    version_id = payload.version_id or tool.current_version_id
    if not version_id:
        raise HTTPException(status_code=400, detail="No version specified")
    version = await session.get(ToolVersion, version_id)
    if not version or version.tool_id != tool_id:
        raise HTTPException(status_code=400, detail="Invalid version")
    tool.status = ToolStatus.BUILDING
    await session.commit()
    execute_build.delay(tool_id, version_id, version.app_py, version.requirements_txt)
    return {"status": "queued"}


@app.post("/v1/tools/{tool_id}/run")
async def run_tool(
    tool_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tool = await session.get(Tool, tool_id)
    if not tool or tool.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    if not tool.current_image_ref:
        raise HTTPException(status_code=400, detail="No built image")
    build = (
        await session.execute(
            select(ToolBuild).where(ToolBuild.image_ref == tool.current_image_ref).order_by(ToolBuild.created_at.desc())
        )
    ).scalars().first()
    if not build:
        raise HTTPException(status_code=400, detail="Build not found")
    execute_run.delay(tool_id, build.id, tool.current_image_ref)
    return {"status": "starting"}


@app.post("/v1/tools/{tool_id}/stop")
async def stop_tool(
    tool_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    tool = await session.get(Tool, tool_id)
    if not tool or tool.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Tool not found")
    execute_stop.delay(tool_id)
    return {"status": "stopping"}
