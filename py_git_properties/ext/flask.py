"""Flask integration for py-git-properties.

Provides ready-to-register Blueprint for health checks and Spring Boot Actuator
style /info endpoints.

Usage:
    from flask import Flask
    from py_git_properties.ext.flask import get_git_info_blueprint

    app = Flask(__name__)
    app.register_blueprint(get_git_info_blueprint(url_prefix="/actuator"))
    # Exposes GET /actuator/info
"""

from typing import Any, Dict, Optional
from ..core import git_info_as_json


def get_git_info_blueprint(
    name: str = "git_info",
    rule: str = "/info",
    url_prefix: Optional[str] = None,
    cached: bool = True,
    custom_git_prop: Optional[Dict[str, Any]] = None,
    dir: Optional[str] = None,
):
    """Create a Flask Blueprint exposing git repository metadata.

    Args:
        name: Blueprint name (default: "git_info").
        rule: URL rule path (default: "/info").
        url_prefix: Blueprint URL prefix (default: None).
        cached: If True, caches git metadata in-memory on first request or initialization.
        custom_git_prop: Optional dictionary of custom properties to merge.
        dir: Target git repository directory.

    Returns:
        flask.Blueprint instance.
    """
    try:
        from flask import Blueprint, jsonify
    except ImportError as e:
        raise ImportError(
            "Flask is required to use py_git_properties.ext.flask. "
            "Install it via: pip install flask"
        ) from e

    bp = Blueprint(name, __name__, url_prefix=url_prefix)
    cache: Dict[str, Any] = {}

    if cached:
        try:
            cache["data"] = git_info_as_json(custom_git_prop, require_object=True, dir=dir)
        except Exception:
            pass

    @bp.route(rule, methods=["GET"])
    def get_git_info():
        if cached and "data" in cache:
            return jsonify(cache["data"])

        data = git_info_as_json(custom_git_prop, require_object=True, dir=dir)
        if cached:
            cache["data"] = data
        return jsonify(data)

    return bp
