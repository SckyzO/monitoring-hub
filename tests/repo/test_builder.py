"""Distribution builder: URL/codename helpers + ./public + ./release assembly."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from forge.domain.artifact import Artifact
from forge.domain.catalog import Catalog, CatalogEntry
from forge.domain.errors import DistributionError
from forge.packaging.runner import CommandResult
from forge.repo.builder import artifact_hosted_url, build_distribution
from forge.repo.naming import codename_for
from tests.fetch.conftest import FakeDownloader

PB = "https://github.com/SckyzO/monitoring-hub/releases/download"
PG = "https://sckyzo.github.io/monitoring-hub"


# --- pure helpers -----------------------------------------------------------


def test_codename_for_known() -> None:
    assert codename_for("ubuntu-24.04") == "noble"
    assert codename_for("debian-13") == "trixie"
    assert codename_for("ubuntu-26.04") == "resolute"


def test_codename_for_unknown_raises() -> None:
    with pytest.raises(DistributionError, match="codename"):
        codename_for("fedora-40")


def test_url_rpm_translates_arch_and_tags_by_target_arch() -> None:
    art = Artifact(type="rpm", target="el9", arch="amd64", sha256="x")
    url = artifact_hosted_url(
        name="node_exporter", version="1.9.1", artifact=art, package_base_url=PB, pages_base_url=PG
    )
    assert url == f"{PB}/rpm-el9-x86_64/node_exporter-1.9.1-1.el9.x86_64.rpm"


def test_url_deb_hyphenates_name_keeps_goarch() -> None:
    art = Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="x")
    url = artifact_hosted_url(
        name="node_exporter", version="1.9.1", artifact=art, package_base_url=PB, pages_base_url=PG
    )
    assert url == f"{PB}/apt-noble/node-exporter_1.9.1-1_amd64.deb"


def test_url_dashboard_points_at_pages() -> None:
    art = Artifact(type="grafana-dashboard", sha256="x")
    url = artifact_hosted_url(
        name="node-overview", version="1.0", artifact=art, package_base_url=PB, pages_base_url=PG
    )
    assert url == f"{PG}/dashboards/node-overview.json"


def test_url_docker_is_none() -> None:
    art = Artifact(type="docker", arch="amd64", sha256="x")
    url = artifact_hosted_url(
        name="node_exporter", version="1.9.1", artifact=art, package_base_url=PB, pages_base_url=PG
    )
    assert url is None


def test_url_rpm_unknown_arch_raises() -> None:
    art = Artifact(type="rpm", target="el9", arch="s390x", sha256="x")
    with pytest.raises(DistributionError, match="arch"):
        artifact_hosted_url(
            name="x", version="1", artifact=art, package_base_url=PB, pages_base_url=PG
        )


# --- orchestration ----------------------------------------------------------


class SentinelRunner:
    """Fake runner emulating createrepo_c / apt-ftparchive / gpg side effects."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        stdin: str | None = None,
    ) -> CommandResult:
        self.calls.append(list(args))
        exe = args[0]
        if exe == "createrepo_c":
            repodata = Path(args[-1]) / "repodata"
            repodata.mkdir(parents=True, exist_ok=True)
            (repodata / "repomd.xml").write_text("<repomd/>")
            return CommandResult(args=list(args), returncode=0, stdout="", stderr="")
        if exe == "apt-ftparchive":
            out = "Package: x\n" if args[1] == "packages" else "Origin: monitoring-hub\n"
            return CommandResult(args=list(args), returncode=0, stdout=out, stderr="")
        if exe == "gpg":
            out_path = Path(args[args.index("--output") + 1])
            out_path.write_text("sig")
            return CommandResult(args=list(args), returncode=0, stdout="", stderr="")
        return CommandResult(args=list(args), returncode=0, stdout="", stderr="")


def _stage(packages_dir: Path, rel: str, fn: str) -> None:
    target = packages_dir / rel
    target.mkdir(parents=True, exist_ok=True)
    (target / fn).write_bytes(b"pkg")


def _catalog() -> Catalog:
    exporter = CatalogEntry(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        category="System",
        description="d",
        artifacts=[
            Artifact(type="rpm", target="el9", arch="amd64", sha256="a"),
            Artifact(type="deb", target="ubuntu-24.04", arch="amd64", sha256="b"),
            Artifact(type="docker", arch="amd64", sha256="c"),
        ],
    )
    dashboard = CatalogEntry(
        kind="dashboard",
        name="node-overview",
        version="1.0",
        category="System",
        description="d",
        artifacts=[Artifact(type="grafana-dashboard", sha256="e")],
    )
    return Catalog(generated_at="2026-06-07T00:00:00Z", items=[exporter, dashboard])


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    packages = tmp_path / "dist"
    _stage(packages, "rpm/el9/amd64", "node_exporter-1.9.1-1.el9.x86_64.rpm")
    _stage(packages, "deb/ubuntu-24.04/amd64", "node-exporter_1.9.1-1_amd64.deb")
    dashboards = tmp_path / "dashboards"
    dashboards.mkdir()
    (dashboards / "node-overview.json").write_text("{}")
    return packages, dashboards


def test_build_distribution_materializes_public_and_release(tmp_path: Path) -> None:
    packages, dashboards = _setup(tmp_path)
    public, release = tmp_path / "public", tmp_path / "release"
    out = build_distribution(
        catalog=_catalog(),
        packages_dir=packages,
        dashboards_dir=dashboards,
        public_out=public,
        release_out=release,
        package_base_url="https://gh/r/download",
        pages_base_url="https://pg",
        runner=SentinelRunner(),
    )
    # Pages tree
    assert (public / "el9" / "x86_64" / "repodata" / "repomd.xml").is_file()
    assert (public / "dashboards" / "node-overview.json").is_file()
    assert (public / "catalog.json").is_file()
    # Releases staging
    assert (release / "rpm-el9-x86_64" / "node_exporter-1.9.1-1.el9.x86_64.rpm").is_file()
    assert (release / "apt-noble" / "node-exporter_1.9.1-1_amd64.deb").is_file()
    assert (release / "apt-noble" / "Packages").is_file()
    assert (release / "apt-noble" / "Release").is_file()
    # URLs populated on the returned catalog
    urls = {a.type: a.url for it in out.items for a in it.artifacts}
    assert (
        urls["rpm"] == "https://gh/r/download/rpm-el9-x86_64/node_exporter-1.9.1-1.el9.x86_64.rpm"
    )
    assert urls["deb"] == "https://gh/r/download/apt-noble/node-exporter_1.9.1-1_amd64.deb"
    assert urls["grafana-dashboard"] == "https://pg/dashboards/node-overview.json"
    assert urls["docker"] is None
    written = json.loads((public / "catalog.json").read_text())
    written_rpm_url = written["items"][0]["artifacts"][0]["url"]
    assert written_rpm_url.endswith("node_exporter-1.9.1-1.el9.x86_64.rpm")


def test_build_distribution_unsigned_skips_gpg(tmp_path: Path) -> None:
    packages, dashboards = _setup(tmp_path)
    runner = SentinelRunner()
    build_distribution(
        catalog=_catalog(),
        packages_dir=packages,
        dashboards_dir=dashboards,
        public_out=tmp_path / "public",
        release_out=tmp_path / "release",
        package_base_url="https://gh/r/download",
        pages_base_url="https://pg",
        runner=runner,
    )
    assert not any(call[0] == "gpg" for call in runner.calls)


def test_build_distribution_signed_signs_repomd_and_release(tmp_path: Path) -> None:
    packages, dashboards = _setup(tmp_path)
    public, release = tmp_path / "public", tmp_path / "release"
    runner = SentinelRunner()
    build_distribution(
        catalog=_catalog(),
        packages_dir=packages,
        dashboards_dir=dashboards,
        public_out=public,
        release_out=release,
        key_id="ABCD",
        package_base_url="https://gh/r/download",
        pages_base_url="https://pg",
        runner=runner,
    )
    assert (public / "el9" / "x86_64" / "repodata" / "repomd.xml.asc").is_file()
    assert (release / "apt-noble" / "InRelease").is_file()
    assert (release / "apt-noble" / "Release.gpg").is_file()
    assert any(
        call[0] == "createrepo_c"
        and "--location-prefix" in call
        and "https://gh/r/download/rpm-el9-x86_64/" in call
        for call in runner.calls
    )


def test_build_distribution_copies_public_key_when_given(tmp_path: Path) -> None:
    packages, dashboards = _setup(tmp_path)
    key = tmp_path / "pub.asc"
    key.write_text("KEY")
    public = tmp_path / "public"
    build_distribution(
        catalog=_catalog(),
        packages_dir=packages,
        dashboards_dir=dashboards,
        public_out=public,
        release_out=tmp_path / "release",
        public_key=key,
        package_base_url="https://gh/r/download",
        pages_base_url="https://pg",
        runner=SentinelRunner(),
    )
    assert (public / "RPM-GPG-KEY-monitoring-hub").read_text() == "KEY"
    assert (public / "apt" / "monitoring-hub.asc").read_text() == "KEY"


def test_build_distribution_missing_package_raises(tmp_path: Path) -> None:
    _, dashboards = _setup(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(DistributionError, match="not found"):
        build_distribution(
            catalog=_catalog(),
            packages_dir=empty,
            dashboards_dir=dashboards,
            public_out=tmp_path / "public",
            release_out=tmp_path / "release",
            package_base_url="https://gh/r/download",
            pages_base_url="https://pg",
            runner=SentinelRunner(),
        )


def test_build_distribution_merge_indexes_only_built_items(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Two rpm items sharing the el9/amd64 coordinate; only A is built this run.
    item_a = CatalogEntry(
        kind="exporter",
        name="node_exporter",
        version="1.9.1",
        category="System",
        description="d",
        artifacts=[
            Artifact(
                type="rpm",
                target="el9",
                arch="amd64",
                sha256="a",
                url=f"{PB}/rpm-el9-x86_64/node_exporter-1.9.1-1.el9.x86_64.rpm",
            )
        ],
    )
    item_b = CatalogEntry(
        kind="exporter",
        name="mysqld_exporter",
        version="0.15.0",
        category="Database",
        description="d",
        artifacts=[
            Artifact(
                type="rpm",
                target="el9",
                arch="amd64",
                sha256="b",
                url=f"{PB}/rpm-el9-x86_64/mysqld_exporter-0.15.0-1.el9.x86_64.rpm",
            )
        ],
    )
    catalog = Catalog(generated_at="2026-06-07T00:00:00Z", items=[item_a, item_b])

    packages = tmp_path / "dist"
    _stage(packages, "rpm/el9/amd64", "node_exporter-1.9.1-1.el9.x86_64.rpm")  # only A
    dashboards = tmp_path / "dashboards"
    dashboards.mkdir()

    merged_pkgs: list[str] = []

    def fake_merge_rpm_repo(**kw: object) -> Path:
        pkg = kw["new_package"]
        assert isinstance(pkg, Path)
        merged_pkgs.append(pkg.name)
        repodata_dir = kw["repodata_dir"]
        assert isinstance(repodata_dir, Path)
        return repodata_dir

    def fail_build_rpm_repo(**kw: object) -> Path:  # pragma: no cover - guard
        raise AssertionError("full build_rpm_repo must not run in merge mode")

    monkeypatch.setattr(
        "forge.repo.builder.fetch_published_repodata", lambda **kw: kw["dest"]
    )
    monkeypatch.setattr("forge.repo.builder.fetch_published_packages", lambda **kw: None)
    monkeypatch.setattr("forge.repo.builder.merge_rpm_repo", fake_merge_rpm_repo)
    monkeypatch.setattr(
        "forge.repo.builder.merge_apt_repo", lambda **kw: kw["repo_dir"]
    )
    monkeypatch.setattr("forge.repo.builder.build_rpm_repo", fail_build_rpm_repo)

    out = build_distribution(
        catalog=catalog,
        packages_dir=packages,
        dashboards_dir=dashboards,
        public_out=tmp_path / "public",
        release_out=tmp_path / "release",
        package_base_url=PB,
        pages_base_url=PG,
        merge=True,
        downloader=FakeDownloader(present=True),
        runner=SentinelRunner(),
    )

    # Only item A's package was merged (B was not built this run).
    assert merged_pkgs == ["node_exporter-1.9.1-1.el9.x86_64.rpm"]
    # Item B's artifacts (URLs) are carried over unchanged.
    returned = {it.name: it for it in out.items}
    assert returned["mysqld_exporter"].artifacts == item_b.artifacts


def test_build_distribution_missing_dashboard_raises(tmp_path: Path) -> None:
    packages, _ = _setup(tmp_path)
    empty = tmp_path / "nodash"
    empty.mkdir()
    with pytest.raises(DistributionError, match="dashboard"):
        build_distribution(
            catalog=_catalog(),
            packages_dir=packages,
            dashboards_dir=empty,
            public_out=tmp_path / "public",
            release_out=tmp_path / "release",
            package_base_url="https://gh/r/download",
            pages_base_url="https://pg",
            runner=SentinelRunner(),
        )
