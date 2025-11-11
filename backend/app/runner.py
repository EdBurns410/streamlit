from typing import Optional

import httpx

from .config import get_settings

settings = get_settings()


async def trigger_build(tool_id: int, version_id: int, app_py: str, requirements_txt: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.runner_url}/build",
            json={
                "tool_id": tool_id,
                "version_id": version_id,
                "app_py": app_py,
                "requirements_txt": requirements_txt,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()


async def trigger_run(tool_id: int, image_ref: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.runner_url}/run",
            json={"tool_id": tool_id, "image_ref": image_ref},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()


async def trigger_stop(tool_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.runner_url}/stop",
            json={"tool_id": tool_id},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
