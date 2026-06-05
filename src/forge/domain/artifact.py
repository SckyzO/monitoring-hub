"""Artifact: a single build output (spec §6.3).

One ``kind`` can yield many artifacts (an exporter → RPM el8/el9/el10 × arch,
DEB, Docker image; a dashboard → one). ``url`` is populated at publish time
(SP2); ``signed`` at signing time.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Artifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    target: str | None = None
    arch: str | None = None
    url: str | None = None
    sha256: str
    signed: bool = False
