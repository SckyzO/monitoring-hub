"""Domain manifest models (spec §6, §7).

A manifest is a common envelope (``ManifestBase``) plus a per-kind ``spec``.
The public ``Manifest`` type is a discriminated union on ``kind``; adding a
kind = a new ``ManifestBase`` subclass + a producer, no core change.

The exporter spec is a faithful port of the legacy marshmallow manifest
contract (upstream / build / artifacts.{rpm,deb,docker}); the upstream
``@validates_schema`` rules are reproduced as a ``model_validator``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

from forge.domain.errors import ManifestError

# --- shared leaf models -----------------------------------------------------


class FileInstall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    dest: str
    mode: str = "0644"
    config: bool = False


class Directory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    mode: str = "0755"
    owner: str = "root"
    group: str = "root"


class Systemd(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    arguments: list[str] = Field(default_factory=list)
    after: list[str] = Field(default_factory=lambda: ["network.target"])
    restart: str = "on-failure"
    type: str = "simple"


class Validation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    port: int | None = None
    command: str | None = None
    args: str | None = None


class ExtraSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    filename: str


class Upstream(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["github", "local"]
    repo: str | None = None
    strategy: str = "latest_release"
    archive_name: str | dict[str, str] | None = None
    local_binary: str | None = None
    local_archive: str | None = None

    @model_validator(mode="after")
    def _check_type_specific(self) -> "Upstream":
        if self.type == "github":
            if not self.repo:
                raise ValueError("'repo' is required for upstream type 'github'")
        else:  # local
            if not self.local_binary and not self.local_archive:
                raise ValueError(
                    "'local_binary' or 'local_archive' required for upstream type 'local'"
                )
            if self.local_binary and self.local_archive:
                raise ValueError("only one of 'local_binary' or 'local_archive' allowed")
        return self


class Build(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["binary_repack", "source_build"]
    binary_name: str
    extra_binaries: list[str] = Field(default_factory=list)
    extra_sources: list[ExtraSource] = Field(default_factory=list)
    archs: list[str] = Field(default_factory=lambda: ["amd64", "arm64"])


# --- exporter spec ----------------------------------------------------------

# Default AUTO-build distro policy. These drive what the unattended pipeline
# builds when a manifest omits `targets`. Dropped distros (el8, ubuntu-22.04)
# are NOT forbidden — `targets` accepts any string, so they stay buildable by
# hand; they are simply out of the automatic default set. Single edit point.
DEFAULT_RPM_TARGETS: tuple[str, ...] = ("el9", "el10")
DEFAULT_DEB_TARGETS: tuple[str, ...] = ("ubuntu-24.04", "ubuntu-26.04", "debian-12", "debian-13")


class RpmTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    targets: list[str] = Field(default_factory=lambda: list(DEFAULT_RPM_TARGETS))
    summary: str | None = None
    install_path: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    systemd: Systemd = Field(default_factory=Systemd)
    system_user: str | None = None
    extra_files: list[FileInstall] = Field(default_factory=list)
    directories: list[Directory] = Field(default_factory=list)


class DebTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    targets: list[str] = Field(default_factory=lambda: list(DEFAULT_DEB_TARGETS))
    summary: str | None = None
    systemd: Systemd = Field(default_factory=Systemd)
    system_user: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    extra_files: list[FileInstall] = Field(default_factory=list)
    directories: list[Directory] = Field(default_factory=list)
    section: str = "utils"
    priority: str = "optional"


class DockerTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    base_image: str = "registry.access.redhat.com/ubi9/ubi-minimal"
    entrypoint: list[str] = Field(default_factory=list)
    cmd: list[str] = Field(default_factory=list)
    validation: Validation = Field(default_factory=Validation)


class ExporterArtifacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rpm: RpmTarget | None = None
    deb: DebTarget | None = None
    docker: DockerTarget | None = None


class ExporterSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    upstream: Upstream
    build: Build
    artifacts: ExporterArtifacts


# --- dashboard spec ---------------------------------------------------------


class GrafanaSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["grafana"]
    id: int
    revision: int


class UrlSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["url"]
    url: str


class GitSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["git"]
    repo: str
    ref: str
    path: str


class LocalSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["local"]
    path: str


DashboardSource = Annotated[
    GrafanaSource | UrlSource | GitSource | LocalSource,
    Field(discriminator="type"),
]


class DashboardSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: DashboardSource
    datasource: str | None = None
    tags: list[str] = Field(default_factory=list)


# --- common envelope --------------------------------------------------------


class ManifestBase(BaseModel):
    """Fields shared by every kind (spec §6.1)."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    name: str
    description: str
    category: str = "System"
    version: str
    license: str | None = None


# --- per-kind manifests + discriminated union -------------------------------


class ExporterManifest(ManifestBase):
    kind: Literal["exporter"]
    spec: ExporterSpec


class DashboardManifest(ManifestBase):
    kind: Literal["dashboard"]
    spec: DashboardSpec


Manifest = Annotated[
    ExporterManifest | DashboardManifest,
    Field(discriminator="kind"),
]

_MANIFEST_ADAPTER: TypeAdapter[Manifest] = TypeAdapter(Manifest)


def parse_manifest(data: Mapping[str, object]) -> Manifest:
    """Validate a raw mapping into a typed ``Manifest`` (discriminated on kind).

    Wraps Pydantic's ``ValidationError`` in ``ManifestError`` so callers catch
    one domain error type (spec §14). The error message keeps the full Pydantic
    report (which field, which item).
    """
    try:
        return _MANIFEST_ADAPTER.validate_python(data)
    except ValidationError as exc:
        raise ManifestError(str(exc)) from exc
