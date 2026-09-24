"""FastAPI / Starlette integration for py-git-properties.

Provides ready-to-mount APIRouter for health checks and Spring Boot Actuator
style /info endpoints.

Usage:
    from fastapi import FastAPI
    from py_git_properties.ext.fastapi import get_git_info_router

    app = FastAPI()
    app.include_router(get_git_info_router(prefix="/actuator"))
    # Exposes GET /actuator/info
"""

from typing import Any, Dict, Optional
from ..core import git_info_as_json_async, git_info_as_json


def get_git_info_router(
    path: str = "/info",
    prefix: str = "",
    tags: Optional[list] = None,
    cached: bool = True,
    custom_git_prop: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
):
    """Create a FastAPI APIRouter exposing git repository metadata.

    Args:
        path: Route path (default: "/info").
        prefix: Router prefix (default: "").
        tags: OpenAPI tags (default: ["actuator"]).
        cached: If True, caches git metadata in-memory on first request or initialization.
        custom_git_prop: Optional dictionary of custom properties to merge.
        dir: Target git repository directory.

    Returns:
        fastapi.APIRouter instance.
    """
    try:
        from fastapi import APIRouter
    except ImportError as e:
        raise ImportError(
            "FastAPI is required to use py_git_properties.ext.fastapi. "
            "Install it via: pip install fastapi"
        ) from e

    router = APIRouter(prefix=prefix, tags=tags or ["actuator"])
    cache: Dict[str, Any] = {}

    if cached:
        try:
            cache["data"] = git_info_as_json(custom_git_prop, require_object=True, dir=dir)
        except Exception:
            pass

    @router.get(path, summary="Git Repository & Build Info")
    async def get_git_info():
        if cached and "data" in cache:
            return cache["data"]

        data = await git_info_as_json_async(custom_git_prop, require_object=True, dir=dir)
        if cached:
            cache["data"] = data
        return data

    return router
