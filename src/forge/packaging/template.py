"""Jinja2 template seam for custom Dockerfiles (spec §7.1 extension point).

A manifest may opt into a fully custom Docker image via
``artifacts.docker.dockerfile``; this renders that template with the manifest as
context. ``StrictUndefined`` makes a typo in a template fail loudly instead of
silently rendering an empty token. Templates are repo-controlled (not network
input), so no autoescape (Dockerfiles are not HTML) and no sandbox is needed.

This is the open/closed extension point for any future custom Dockerfile: a new
exotic image is a new template file, with no engine change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateError
from jinja2.exceptions import UndefinedError

from forge.domain.errors import BuildError


def render_template(template_path: Path, context: dict[str, Any]) -> str:
    if not template_path.is_file():
        raise BuildError(f"custom Dockerfile template not found: {template_path}")
    try:
        source = template_path.read_text(encoding="utf-8")
        env = Environment(  # noqa: S701 — Dockerfile, not HTML
            undefined=StrictUndefined, autoescape=False, keep_trailing_newline=True
        )
        return env.from_string(source).render(**context)
    except UndefinedError as exc:
        raise BuildError(f"undefined variable in {template_path.name}: {exc}") from exc
    except TemplateError as exc:
        raise BuildError(f"failed to render {template_path.name}: {exc}") from exc
