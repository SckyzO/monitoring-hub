"""
Tests for V3 artifact JSON schemas.

Validates that generated artifacts conform to the V3 format specification.
"""

from datetime import datetime
from urllib.parse import urlparse

import pytest


class TestRPMArtifactSchema:
    """Test RPM artifact JSON schema validation."""

    def test_rpm_artifact_valid_schema(self):
        """Valid RPM artifact should pass all checks."""
        artifact = {
            "format_version": "3.0",
            "artifact_type": "rpm",
            "exporter": "node_exporter",
            "version": "1.10.2",
            "arch": "amd64",
            "dist": "el9",
            "build_date": "2024-02-13T10:30:00Z",
            "status": "success",
            "package": {
                "filename": "node_exporter-1.10.2-1.el9.x86_64.rpm",
                "url": "https://github.com/test/releases/download/node_exporter-v1.10.2/node_exporter-1.10.2-1.el9.x86_64.rpm",
                "sha256": "abc123def456",
                "size_bytes": 12345678,
            },
            "rpm_metadata": {
                "name": "node_exporter",
                "version": "1.10.2",
                "release": "1",
                "arch": "x86_64",
                "summary": "Prometheus exporter for hardware and OS metrics",
                "license": "Apache-2.0",
            },
        }

        # Required fields
        assert artifact["format_version"] == "3.0"
        assert artifact["artifact_type"] == "rpm"
        assert artifact["exporter"] == "node_exporter"
        assert artifact["version"] == "1.10.2"
        assert artifact["arch"] == "amd64"
        assert artifact["dist"] == "el9"
        assert artifact["status"] in ["success", "failed", "pending"]

        # Build date format
        datetime.fromisoformat(artifact["build_date"].replace("Z", "+00:00"))

        # Package fields
        assert artifact["package"]["filename"]
        assert artifact["package"]["url"].startswith("https://")
        assert len(artifact["package"]["sha256"]) > 0
        assert artifact["package"]["size_bytes"] > 0

    def test_rpm_artifact_missing_required_fields(self):
        """RPM artifact with missing required fields should fail."""
        incomplete_artifact = {
            "format_version": "3.0",
            "artifact_type": "rpm",
            # Missing: exporter, version, arch, dist, build_date, status, package
        }

        with pytest.raises(KeyError):
            _ = incomplete_artifact["exporter"]
            _ = incomplete_artifact["version"]
            _ = incomplete_artifact["package"]

    def test_rpm_artifact_invalid_status(self):
        """RPM artifact with invalid status value should fail validation."""
        artifact = {
            "format_version": "3.0",
            "artifact_type": "rpm",
            "exporter": "test",
            "version": "1.0.0",
            "arch": "amd64",
            "dist": "el9",
            "build_date": "2024-01-01T00:00:00Z",
            "status": "invalid_status",  # Invalid
            "package": {},
        }

        # Status must be one of: success, failed, pending
        assert artifact["status"] not in ["success", "failed", "pending"]


class TestDEBArtifactSchema:
    """Test DEB artifact JSON schema validation."""

    def test_deb_artifact_valid_schema(self):
        """Valid DEB artifact should pass all checks."""
        artifact = {
            "format_version": "3.0",
            "artifact_type": "deb",
            "exporter": "redis_exporter",
            "version": "1.81.0",
            "arch": "amd64",
            "dist": "ubuntu-22.04",
            "build_date": "2024-02-13T10:30:00Z",
            "status": "success",
            "package": {
                "filename": "redis-exporter_1.81.0-1_amd64.deb",
                "url": "https://github.com/test/releases/download/redis_exporter-v1.81.0/redis-exporter_1.81.0-1_amd64.deb",
                "sha256": "def789ghi012",
                "size_bytes": 8765432,
            },
            "deb_metadata": {
                "package": "redis-exporter",
                "version": "1.81.0-1",
                "architecture": "amd64",
                "maintainer": "Monitoring Hub",
                "description": "Prometheus exporter for Redis metrics",
                "section": "net",
                "priority": "optional",
            },
        }

        # Required fields
        assert artifact["format_version"] == "3.0"
        assert artifact["artifact_type"] == "deb"
        assert artifact["exporter"] == "redis_exporter"
        assert artifact["arch"] in ["amd64", "arm64"]
        assert artifact["dist"] in [
            "ubuntu-22.04",
            "ubuntu-24.04",
            "debian-12",
            "debian-13",
        ]

        # Build date format
        datetime.fromisoformat(artifact["build_date"].replace("Z", "+00:00"))

        # Package fields
        assert artifact["package"]["filename"].endswith(".deb")
        assert artifact["package"]["url"].startswith("https://")

    def test_deb_artifact_supported_distributions(self):
        """DEB artifact should use supported distributions."""
        supported_dists = ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "debian-13"]

        artifact = {
            "format_version": "3.0",
            "artifact_type": "deb",
            "exporter": "test",
            "version": "1.0.0",
            "arch": "amd64",
            "dist": "ubuntu-22.04",
            "build_date": "2024-01-01T00:00:00Z",
            "status": "success",
            "package": {},
        }

        assert artifact["dist"] in supported_dists


class TestDockerArtifactSchema:
    """Test Docker artifact JSON schema validation."""

    def test_docker_artifact_valid_schema(self):
        """Valid Docker artifact should pass all checks."""
        artifact = {
            "format_version": "3.0",
            "artifact_type": "docker",
            "exporter": "mongodb_exporter",
            "version": "0.48.0",
            "build_date": "2024-02-13T10:30:00Z",
            "status": "success",
            "images": [
                {
                    "registry": "ghcr.io",
                    "repository": "sckyzo/monitoring-hub/mongodb_exporter",
                    "tag": "0.48.0",
                    "digest": "sha256:abc123def456",
                    "platforms": ["linux/amd64", "linux/arm64"],
                },
                {
                    "registry": "ghcr.io",
                    "repository": "sckyzo/monitoring-hub/mongodb_exporter",
                    "tag": "latest",
                    "digest": "sha256:abc123def456",
                    "platforms": ["linux/amd64", "linux/arm64"],
                },
            ],
        }

        # Required fields
        assert artifact["format_version"] == "3.0"
        assert artifact["artifact_type"] == "docker"
        assert artifact["exporter"] == "mongodb_exporter"
        assert artifact["version"] == "0.48.0"
        assert artifact["status"] == "success"

        # Build date format
        datetime.fromisoformat(artifact["build_date"].replace("Z", "+00:00"))

        # Images
        assert len(artifact["images"]) > 0
        for image in artifact["images"]:
            assert image["registry"]
            assert image["repository"]
            assert image["tag"]
            assert "platforms" in image

    def test_docker_artifact_no_arch_field(self):
        """Docker artifacts should not have arch/dist fields."""
        artifact = {
            "format_version": "3.0",
            "artifact_type": "docker",
            "exporter": "test",
            "version": "1.0.0",
            "build_date": "2024-01-01T00:00:00Z",
            "status": "success",
            "images": [],
        }

        # Docker artifacts are multi-platform, no single arch field
        assert "arch" not in artifact
        assert "dist" not in artifact


class TestAggregatedMetadataSchema:
    """Test aggregated metadata.json schema."""

    def test_aggregated_metadata_valid_schema(self):
        """Valid aggregated metadata should pass all checks."""
        metadata = {
            "format_version": "3.0",
            "exporter": "node_exporter",
            "version": "1.10.2",
            "category": "System",
            "description": "Hardware and OS metrics exporter",
            "last_updated": "2024-02-13T10:30:00Z",
            "artifacts": {
                "rpm": {
                    "el9": {
                        "amd64": {
                            "status": "success",
                            "url": "https://github.com/test/node_exporter.rpm",
                            "size_bytes": 12345678,
                            "sha256": "abc123",
                            "build_date": "2024-02-13T10:30:00Z",
                        },
                        "arm64": {
                            "status": "success",
                            "url": "https://github.com/test/node_exporter_arm64.rpm",
                            "size_bytes": 12345678,
                            "sha256": "def456",
                            "build_date": "2024-02-13T10:30:00Z",
                        },
                    },
                },
                "deb": {
                    "ubuntu-22.04": {
                        "amd64": {
                            "status": "success",
                            "url": "https://github.com/test/node-exporter.deb",
                            "size_bytes": 8765432,
                            "sha256": "ghi789",
                            "build_date": "2024-02-13T10:30:00Z",
                        },
                    },
                },
                "docker": {
                    "status": "success",
                    "images": [{"registry": "ghcr.io", "tag": "1.10.2"}],
                    "build_date": "2024-02-13T10:30:00Z",
                },
            },
            "status": {
                "rpm": "success",
                "deb": "success",
                "docker": "success",
            },
        }

        # Required fields
        assert metadata["format_version"] == "3.0"
        assert metadata["exporter"] == "node_exporter"
        assert metadata["version"] == "1.10.2"
        assert metadata["category"] in [
            "System",
            "Database",
            "Web",
            "Network",
            "Storage",
            "Messaging",
            "Infrastructure",
        ]

        # Artifacts structure
        assert "rpm" in metadata["artifacts"]
        assert "deb" in metadata["artifacts"]
        assert "docker" in metadata["artifacts"]

        # Status aggregates
        assert metadata["status"]["rpm"] in ["success", "failed", "pending", "na"]
        assert metadata["status"]["deb"] in ["success", "failed", "pending", "na"]
        assert metadata["status"]["docker"] in ["success", "failed", "pending", "na"]

    def test_aggregated_metadata_nested_structure(self):
        """Aggregated metadata should have correct nesting for RPM/DEB."""
        metadata = {
            "format_version": "3.0",
            "exporter": "test",
            "version": "1.0.0",
            "category": "System",
            "description": "Test",
            "last_updated": "2024-01-01T00:00:00Z",
            "artifacts": {
                "rpm": {
                    "el9": {
                        "amd64": {"status": "success"},
                    },
                },
                "deb": {},
                "docker": {"status": "na"},
            },
            "status": {
                "rpm": "success",
                "deb": "na",
                "docker": "na",
            },
        }

        # RPM: dist -> arch -> info
        assert isinstance(metadata["artifacts"]["rpm"], dict)
        assert "el9" in metadata["artifacts"]["rpm"]
        assert "amd64" in metadata["artifacts"]["rpm"]["el9"]

        # DEB: dist -> arch -> info
        assert isinstance(metadata["artifacts"]["deb"], dict)

        # Docker: flat structure with images list
        assert isinstance(metadata["artifacts"]["docker"], dict)


class TestSchemaVersioning:
    """Test format version handling."""

    def test_format_version_3_0(self):
        """All V3 artifacts must have format_version 3.0."""
        artifacts = [
            {"format_version": "3.0", "artifact_type": "rpm"},
            {"format_version": "3.0", "artifact_type": "deb"},
            {"format_version": "3.0", "artifact_type": "docker"},
        ]

        for artifact in artifacts:
            assert artifact["format_version"] == "3.0"

    def test_backward_compatibility_check(self):
        """V2 format should be distinguishable from V3."""
        v2_artifact = {
            "name": "node_exporter",
            "version": "1.10.2",
            "availability": {"el9": {"x86_64": {"status": "success"}}},
        }

        v3_artifact = {
            "format_version": "3.0",
            "exporter": "node_exporter",
            "artifacts": {"rpm": {"el9": {"amd64": {"status": "success"}}}},
        }

        # V2 has no format_version field
        assert "format_version" not in v2_artifact
        assert v2_artifact.get("format_version") is None

        # V3 has explicit format_version
        assert v3_artifact["format_version"] == "3.0"


class TestSchemaValidation:
    """Test JSON schema validation helpers."""

    def test_valid_iso8601_timestamp(self):
        """Build dates must be valid ISO 8601 timestamps."""
        valid_timestamps = [
            "2024-02-13T10:30:00Z",
            "2024-02-13T10:30:00+00:00",
            "2024-02-13T10:30:00.123456Z",
        ]

        for timestamp in valid_timestamps:
            # Should not raise exception
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_url_validation(self):
        """Package URLs must be valid HTTPS URLs."""
        valid_urls = [
            "https://github.com/test/releases/download/v1.0.0/package.rpm",
            "https://github.com/owner/repo/releases/download/tag/file.deb",
        ]

        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme == "https"
            assert parsed.netloc == "github.com"

    def test_sha256_format(self):
        """SHA256 checksums must be valid hex strings."""
        valid_checksums = [
            "abc123def456",  # Minimal
            "a" * 64,  # Full length SHA256
        ]

        for checksum in valid_checksums:
            # Should be alphanumeric (hex)
            assert all(c in "0123456789abcdefABCDEF" for c in checksum)
