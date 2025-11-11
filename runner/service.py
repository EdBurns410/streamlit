import os
import tempfile
from pathlib import Path

import docker
from docker import errors as docker_errors
from fastapi import FastAPI, HTTPException

BASE_IMAGE = os.getenv("SHEETIFY_BASE_IMAGE", "sheetify-base:latest")
TRAEFIK_NETWORK = os.getenv("TRAEFIK_NETWORK", "web")
TRAEFIK_ENTRYPOINT = os.getenv("TRAEFIK_ENTRYPOINT", "web")

client = docker.from_env()
app = FastAPI(title="Sheetify Runner")


def _build_image(tool_id: int, version_id: int, app_py: str, requirements_txt: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "app.py").write_text(app_py)
        (tmp / "requirements.txt").write_text(requirements_txt)
        dockerfile = tmp / "Dockerfile"
        dockerfile.write_text(
            f"FROM {BASE_IMAGE}\n"
            "WORKDIR /workspace\n"
            "COPY requirements.txt requirements.txt\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY app.py app.py\n"
        )
        tag = f"sheetify-tool-{tool_id}:v{version_id}"
        logs = []
        image, build_logs = client.images.build(path=tmpdir, tag=tag, rm=True)
        for chunk in build_logs:
            line = chunk.get("stream") or chunk.get("error")
            if line:
                logs.append(line.strip())
        return {"image_ref": tag, "logs": "\n".join(logs)}


def _run_container(tool_id: int, image_ref: str) -> dict:
    tool_path = f"/t/{tool_id}"
    name = f"sheetify-tool-{tool_id}"
    try:
        existing = client.containers.get(name)
        existing.remove(force=True)
    except docker_errors.NotFound:
        pass
    container = client.containers.run(
        image_ref,
        name=name,
        command=[
            "streamlit",
            "run",
            "app.py",
            "--server.headless",
            "true",
            "--server.baseUrlPath",
            tool_path,
            "--server.port",
            "8501",
        ],
        detach=True,
        network=TRAEFIK_NETWORK if TRAEFIK_NETWORK else None,
        labels={
            "traefik.enable": "true",
            f"traefik.http.routers.tool{tool_id}.rule": f"PathPrefix(`{tool_path}`)",
            f"traefik.http.routers.tool{tool_id}.entrypoints": TRAEFIK_ENTRYPOINT,
            f"traefik.http.routers.tool{tool_id}.service": f"tool{tool_id}",
            f"traefik.http.services.tool{tool_id}.loadbalancer.server.port": "8501",
        },
        security_opt=["no-new-privileges"],
        cap_drop=["NET_RAW"],
    )
    return {
        "container_id": container.id,
        "url": f"/t/{tool_id}",
        "logs": "Container started",
    }


def _stop_container(tool_id: int) -> dict:
    name = f"sheetify-tool-{tool_id}"
    try:
        container = client.containers.get(name)
    except docker_errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not running")
    container.stop()
    container.remove()
    return {"status": "stopped"}


@app.post("/build")
def build(payload: dict):
    try:
        return _build_image(
            tool_id=payload["tool_id"],
            version_id=payload["version_id"],
            app_py=payload["app_py"],
            requirements_txt=payload["requirements_txt"],
        )
    except docker_errors.BuildError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/run")
def run(payload: dict):
    try:
        return _run_container(tool_id=payload["tool_id"], image_ref=payload["image_ref"])
    except docker_errors.ContainerError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/stop")
def stop(payload: dict):
    return _stop_container(payload["tool_id"])
