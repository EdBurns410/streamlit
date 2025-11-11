from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio

from .config import get_settings
from .database import AsyncSessionLocal
from .models import BuildStatus, RunStatus, Tool, ToolBuild, ToolRun, ToolStatus
from .runner import trigger_build, trigger_run, trigger_stop

settings = get_settings()

celery_app = Celery(
    "sheetify",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task
def execute_build(tool_id: int, version_id: int, app_py: str, requirements_txt: str) -> None:
    async def _inner():
        async with AsyncSessionLocal() as session:
            build = ToolBuild(version_id=version_id, status=BuildStatus.RUNNING)
            session.add(build)
            await session.flush()
            try:
                await session.execute(
                    select(Tool).where(Tool.id == tool_id).execution_options(populate_existing=True)
                )
                result = await trigger_build(tool_id, version_id, app_py, requirements_txt)
                build.status = BuildStatus.SUCCESS
                build.image_ref = result.get("image_ref")
                build.logs = result.get("logs")
                tool = await session.get(Tool, tool_id)
                if tool:
                    tool.status = ToolStatus.IDLE
                    tool.current_image_ref = build.image_ref
                    tool.current_version_id = version_id
            except Exception as exc:  # pragma: no cover
                build.status = BuildStatus.FAILED
                build.logs = str(exc)
                tool = await session.get(Tool, tool_id)
                if tool:
                    tool.status = ToolStatus.ERROR
            await session.commit()
    _run_async(_inner())


@celery_app.task
def execute_run(tool_id: int, build_id: int, image_ref: str) -> None:
    async def _inner():
        async with AsyncSessionLocal() as session:
            run = ToolRun(tool_id=tool_id, build_id=build_id, status=RunStatus.STARTING)
            session.add(run)
            await session.flush()
            try:
                result = await trigger_run(tool_id, image_ref)
                run.status = RunStatus.RUNNING
                run.container_id = result.get("container_id")
                run.url = result.get("url")
                run.logs = result.get("logs")
                tool = await session.get(Tool, tool_id)
                if tool:
                    tool.status = ToolStatus.RUNNING
            except Exception as exc:  # pragma: no cover
                run.status = RunStatus.FAILED
                run.logs = str(exc)
                tool = await session.get(Tool, tool_id)
                if tool:
                    tool.status = ToolStatus.ERROR
            await session.commit()
    _run_async(_inner())


@celery_app.task
def execute_stop(tool_id: int) -> None:
    async def _inner():
        async with AsyncSessionLocal() as session:
            tool = await session.get(Tool, tool_id)
            if not tool or tool.status != ToolStatus.RUNNING:
                return
            await trigger_stop(tool_id)
            tool.status = ToolStatus.IDLE
            result = await session.execute(
                select(ToolRun).where(ToolRun.tool_id == tool_id).order_by(ToolRun.created_at.desc())
            )
            last_run = result.scalars().first()
            if last_run:
                last_run.status = RunStatus.STOPPED
                last_run.logs = (last_run.logs or "") + "
Stopped by user"
            await session.commit()
    _run_async(_inner())
