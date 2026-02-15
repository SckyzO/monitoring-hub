"""
Tests for metadata aggregation logic.

Tests the aggregate_catalog_metadata.py functionality.
"""

import json


from core.scripts.aggregate_catalog_metadata import (
    aggregate_deb_artifacts,
    aggregate_docker_artifacts,
    aggregate_metadata,
    aggregate_rpm_artifacts,
    compute_aggregate_status,
    find_latest_build_date,
    load_artifacts,
    load_manifest,
)


class TestLoadArtifacts:
    """Test artifact loading from directory."""

    def test_load_artifacts_empty_directory(self, tmp_path):
        """Empty directory should return empty list."""
        artifacts = load_artifacts(tmp_path)
        assert artifacts == []

    def test_load_artifacts_skips_metadata_json(self, tmp_path):
        """Should skip metadata.json to avoid circular dependency."""
        # Create metadata.json
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text(json.dumps({"format_version": "3.0"}))

        # Create actual artifact
        artifact_file = tmp_path / "rpm_amd64_el9.json"
        artifact_file.write_text(
            json.dumps({"artifact_type": "rpm", "format_version": "3.0"})
        )

        artifacts = load_artifacts(tmp_path)

        # Should only load the artifact, not metadata.json
        assert len(artifacts) == 1
        assert artifacts[0]["artifact_type"] == "rpm"

    def test_load_artifacts_multiple_files(self, tmp_path):
        """Should load all artifact JSON files."""
        # Create multiple artifacts
        (tmp_path / "rpm_amd64_el9.json").write_text(
            json.dumps({"artifact_type": "rpm"})
        )
        (tmp_path / "rpm_arm64_el9.json").write_text(
            json.dumps({"artifact_type": "rpm"})
        )
        (tmp_path / "docker.json").write_text(json.dumps({"artifact_type": "docker"}))

        artifacts = load_artifacts(tmp_path)

        assert len(artifacts) == 3
        assert sum(1 for a in artifacts if a["artifact_type"] == "rpm") == 2
        assert sum(1 for a in artifacts if a["artifact_type"] == "docker") == 1


class TestAggregateRPMArtifacts:
    """Test RPM artifact aggregation."""

    def test_aggregate_rpm_basic(self):
        """Basic RPM aggregation should work."""
        artifacts = [
            {
                "artifact_type": "rpm",
                "dist": "el9",
                "arch": "amd64",
                "status": "success",
                "package": {
                    "url": "https://test.com/package.rpm",
                    "size_bytes": 1234,
                    "sha256": "abc123",
                },
                "build_date": "2024-01-01T00:00:00Z",
            }
        ]

        result = aggregate_rpm_artifacts(artifacts)

        assert "el9" in result
        assert "amd64" in result["el9"]
        assert result["el9"]["amd64"]["status"] == "success"
        assert result["el9"]["amd64"]["url"] == "https://test.com/package.rpm"

    def test_aggregate_rpm_multiple_architectures(self):
        """Should handle multiple architectures per dist."""
        artifacts = [
            {
                "artifact_type": "rpm",
                "dist": "el9",
                "arch": "amd64",
                "status": "success",
                "package": {"url": "url1"},
            },
            {
                "artifact_type": "rpm",
                "dist": "el9",
                "arch": "arm64",
                "status": "success",
                "package": {"url": "url2"},
            },
        ]

        result = aggregate_rpm_artifacts(artifacts)

        assert len(result["el9"]) == 2
        assert "amd64" in result["el9"]
        assert "arm64" in result["el9"]

    def test_aggregate_rpm_ignores_non_rpm(self):
        """Should ignore non-RPM artifacts."""
        artifacts = [
            {"artifact_type": "deb", "dist": "ubuntu-22.04", "arch": "amd64"},
            {
                "artifact_type": "rpm",
                "dist": "el9",
                "arch": "amd64",
                "status": "success",
                "package": {},
            },
        ]

        result = aggregate_rpm_artifacts(artifacts)

        assert "el9" in result
        assert "ubuntu-22.04" not in result


class TestAggregateDEBArtifacts:
    """Test DEB artifact aggregation."""

    def test_aggregate_deb_basic(self):
        """Basic DEB aggregation should work."""
        artifacts = [
            {
                "artifact_type": "deb",
                "dist": "ubuntu-22.04",
                "arch": "amd64",
                "status": "success",
                "package": {
                    "url": "https://test.com/package.deb",
                    "size_bytes": 5678,
                    "sha256": "def456",
                },
                "build_date": "2024-01-01T00:00:00Z",
            }
        ]

        result = aggregate_deb_artifacts(artifacts)

        assert "ubuntu-22.04" in result
        assert "amd64" in result["ubuntu-22.04"]
        assert result["ubuntu-22.04"]["amd64"]["status"] == "success"

    def test_aggregate_deb_multiple_distributions(self):
        """Should handle multiple distributions."""
        artifacts = [
            {
                "artifact_type": "deb",
                "dist": "ubuntu-22.04",
                "arch": "amd64",
                "status": "success",
                "package": {},
            },
            {
                "artifact_type": "deb",
                "dist": "debian-12",
                "arch": "amd64",
                "status": "success",
                "package": {},
            },
        ]

        result = aggregate_deb_artifacts(artifacts)

        assert len(result) == 2
        assert "ubuntu-22.04" in result
        assert "debian-12" in result


class TestAggregateDockerArtifacts:
    """Test Docker artifact aggregation."""

    def test_aggregate_docker_basic(self):
        """Basic Docker aggregation should work."""
        artifacts = [
            {
                "artifact_type": "docker",
                "status": "success",
                "images": [
                    {"registry": "ghcr.io", "tag": "1.0.0"},
                    {"registry": "ghcr.io", "tag": "latest"},
                ],
                "build_date": "2024-01-01T00:00:00Z",
            }
        ]

        result = aggregate_docker_artifacts(artifacts)

        assert result["status"] == "success"
        assert len(result["images"]) == 2
        assert result["build_date"] == "2024-01-01T00:00:00Z"

    def test_aggregate_docker_no_artifacts(self):
        """No Docker artifacts should return na status."""
        artifacts = [{"artifact_type": "rpm"}]

        result = aggregate_docker_artifacts(artifacts)

        assert result["status"] == "na"
        assert result["images"] == []
        assert result["build_date"] is None


class TestComputeAggregateStatus:
    """Test aggregate status computation."""

    def test_status_all_success(self):
        """All successful artifacts should result in success status."""
        artifacts_by_type = {
            "rpm": {
                "el9": {
                    "amd64": {"status": "success"},
                    "arm64": {"status": "success"},
                }
            },
            "deb": {"ubuntu-22.04": {"amd64": {"status": "success"}}},
            "docker": {"status": "success"},
        }

        statuses = compute_aggregate_status(artifacts_by_type)

        assert statuses["rpm"] == "success"
        assert statuses["deb"] == "success"
        assert statuses["docker"] == "success"

    def test_status_partial_success(self):
        """At least one success should result in success status."""
        artifacts_by_type = {
            "rpm": {
                "el9": {
                    "amd64": {"status": "success"},
                    "arm64": {"status": "failed"},
                }
            },
            "deb": {},
            "docker": {"status": "na"},
        }

        statuses = compute_aggregate_status(artifacts_by_type)

        assert statuses["rpm"] == "success"  # Has one success

    def test_status_all_failed(self):
        """All failed artifacts should result in failed status."""
        artifacts_by_type = {
            "rpm": {"el9": {"amd64": {"status": "failed"}}},
            "deb": {},
            "docker": {"status": "na"},
        }

        statuses = compute_aggregate_status(artifacts_by_type)

        assert statuses["rpm"] == "failed"

    def test_status_pending(self):
        """Pending artifacts without success should result in pending status."""
        artifacts_by_type = {
            "rpm": {"el9": {"amd64": {"status": "pending"}}},
            "deb": {},
            "docker": {"status": "na"},
        }

        statuses = compute_aggregate_status(artifacts_by_type)

        assert statuses["rpm"] == "pending"

    def test_status_empty_artifacts(self):
        """Empty artifacts should result in na status."""
        artifacts_by_type = {"rpm": {}, "deb": {}, "docker": {"status": "na"}}

        statuses = compute_aggregate_status(artifacts_by_type)

        assert statuses["rpm"] == "na"
        assert statuses["deb"] == "na"


class TestFindLatestBuildDate:
    """Test finding latest build date."""

    def test_latest_build_date_single(self):
        """Single artifact should return its build date."""
        artifacts = [{"build_date": "2024-01-01T00:00:00Z"}]

        latest = find_latest_build_date(artifacts)

        assert latest == "2024-01-01T00:00:00Z"

    def test_latest_build_date_multiple(self):
        """Should return the most recent date."""
        artifacts = [
            {"build_date": "2024-01-01T00:00:00Z"},
            {"build_date": "2024-02-01T00:00:00Z"},  # Latest
            {"build_date": "2024-01-15T00:00:00Z"},
        ]

        latest = find_latest_build_date(artifacts)

        assert latest == "2024-02-01T00:00:00Z"

    def test_latest_build_date_none(self):
        """No build dates should return None."""
        artifacts = [{"no_date": True}]

        latest = find_latest_build_date(artifacts)

        assert latest is None


class TestAggregateMetadata:
    """Test full metadata aggregation."""

    def test_aggregate_metadata_complete(self):
        """Complete aggregation with all artifact types."""
        exporter = "node_exporter"
        artifacts = [
            {
                "artifact_type": "rpm",
                "dist": "el9",
                "arch": "amd64",
                "status": "success",
                "package": {"url": "rpm_url"},
                "build_date": "2024-01-01T00:00:00Z",
            },
            {
                "artifact_type": "deb",
                "dist": "ubuntu-22.04",
                "arch": "amd64",
                "status": "success",
                "package": {"url": "deb_url"},
                "build_date": "2024-01-02T00:00:00Z",
            },
            {
                "artifact_type": "docker",
                "status": "success",
                "images": [],
                "build_date": "2024-01-03T00:00:00Z",
            },
        ]
        manifest = {
            "version": "v1.10.2",
            "category": "System",
            "description": "Test exporter",
        }

        result = aggregate_metadata(exporter, artifacts, manifest)

        assert result["format_version"] == "3.0"
        assert result["exporter"] == "node_exporter"
        assert result["version"] == "1.10.2"  # v stripped
        assert result["category"] == "System"
        assert result["last_updated"] == "2024-01-03T00:00:00Z"  # Latest

        # Artifacts
        assert "rpm" in result["artifacts"]
        assert "deb" in result["artifacts"]
        assert "docker" in result["artifacts"]

        # Statuses
        assert result["status"]["rpm"] == "success"
        assert result["status"]["deb"] == "success"
        assert result["status"]["docker"] == "success"

    def test_aggregate_metadata_strips_version_prefix(self):
        """Version 'v' prefix should be stripped."""
        manifest = {"version": "v1.2.3", "category": "System", "description": "Test"}

        result = aggregate_metadata("test", [], manifest)

        assert result["version"] == "1.2.3"

    def test_aggregate_metadata_default_category(self):
        """Missing category should default to System."""
        manifest = {"version": "1.0.0", "description": "Test"}

        result = aggregate_metadata("test", [], manifest)

        assert result["category"] == "System"


class TestLoadManifest:
    """Test manifest loading."""

    def test_load_manifest_valid(self, tmp_path):
        """Valid manifest should load correctly."""
        manifest_file = tmp_path / "manifest.yaml"
        manifest_file.write_text(
            """
name: test_exporter
version: v1.0.0
category: System
description: Test
"""
        )

        manifest = load_manifest(manifest_file)

        assert manifest["name"] == "test_exporter"
        assert manifest["version"] == "v1.0.0"

    def test_load_manifest_missing_file(self, tmp_path):
        """Missing manifest should return empty dict."""
        manifest = load_manifest(tmp_path / "nonexistent.yaml")

        assert manifest == {}
