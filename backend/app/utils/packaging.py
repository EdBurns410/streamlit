import ast
import io
import zipfile
from pathlib import Path
from typing import Tuple

DANGEROUS_IMPORTS = {"subprocess", "os.system", "socket", "paramiko"}


class PackagingError(Exception):
    pass


def _infer_requirements(source: str) -> str:
    tree = ast.parse(source)
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split(".")[0])
    safe_modules = sorted(
        module
        for module in modules
        if module not in {"streamlit", "os", "sys", "math", "json", "datetime", "pathlib"}
    )
    requirements = ["streamlit>=1.32"]
    for module in safe_modules:
        requirements.append(module)
    return "\n".join(requirements)


def _detect_dangerous(source: str) -> None:
    for banned in DANGEROUS_IMPORTS:
        if banned in source:
            raise PackagingError(f"Dangerous import detected: {banned}")


def load_version_payload(filename: str, data: bytes) -> Tuple[str, str]:
    """Return (app_py, requirements_txt)."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".py":
        source = data.decode("utf-8")
        _detect_dangerous(source)
        requirements = _infer_requirements(source)
        return source, requirements
    if suffix == ".zip":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            app_source = None
            requirements = None
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                path = Path(name)
                content = zf.read(name).decode("utf-8")
                if path.name == "app.py":
                    _detect_dangerous(content)
                    app_source = content
                elif path.name == "requirements.txt":
                    requirements = content
            if app_source is None:
                raise PackagingError("Archive must contain app.py")
            if requirements is None:
                requirements = _infer_requirements(app_source)
            return app_source, requirements
    raise PackagingError("Unsupported file type. Upload .py or .zip")
