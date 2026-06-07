"""Jinja2 template seam for custom Dockerfiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from forge.domain.errors import BuildError
from forge.packaging.template import render_template


def test_render_template_substitutes_context(tmp_path: Path) -> None:
    tpl = tmp_path / "Dockerfile.j2"
    tpl.write_text("FROM {{ base }}\nCOPY {{ name }} /usr/bin/{{ name }}\n", encoding="utf-8")
    out = render_template(tpl, {"base": "ubi9", "name": "node_exporter"})
    assert out == "FROM ubi9\nCOPY node_exporter /usr/bin/node_exporter\n"


def test_render_template_strict_undefined_raises(tmp_path: Path) -> None:
    tpl = tmp_path / "Dockerfile.j2"
    tpl.write_text("FROM {{ missing }}\n", encoding="utf-8")
    with pytest.raises(BuildError, match="undefined"):
        render_template(tpl, {})


def test_render_template_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="not found"):
        render_template(tmp_path / "nope.j2", {})


def test_render_template_syntax_error_raises(tmp_path: Path) -> None:
    tpl = tmp_path / "Dockerfile.j2"
    tpl.write_text("FROM {% if %}\n", encoding="utf-8")
    with pytest.raises(BuildError, match="failed to render"):
        render_template(tpl, {})
