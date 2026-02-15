"""
Tests for site_generator_v2.py.

Tests portal generation with V3 catalog structure.
"""

from core.engine.site_generator_v2 import convert_metadata_to_legacy_format


class TestConvertMetadataToLegacyFormat:
    """Test V3 to legacy format conversion."""

    def test_convert_complete_metadata(self):
        """Complete V3 metadata should convert correctly."""
        metadata = {
            "format_version": "3.0",
            "exporter": "node_exporter",
            "version": "1.10.2",
            "category": "System",
            "description": "Hardware and OS metrics",
            "last_updated": "2024-02-13T10:30:00Z",
            "artifacts": {
                "rpm": {
                    "el9": {
                        "amd64": {
                            "status": "success",
                            "url": "https://test.com/node_exporter.rpm",
                            "size_bytes": 12345,
                            "sha256": "abc123",
                        }
                    }
                },
                "deb": {
                    "ubuntu-22.04": {
                        "amd64": {
                            "status": "success",
                            "url": "https://test.com/node-exporter.deb",
                        }
                    }
                },
                "docker": {"status": "success"},
            },
            "status": {
                "rpm": "success",
                "deb": "success",
                "docker": "success",
            },
        }

        manifest = {
            "name": "node_exporter",
            "version": "1.10.2",
            "readme": "Test README",
        }

        result = convert_metadata_to_legacy_format(metadata, manifest)

        # Basic fields
        assert result["name"] == "node_exporter"
        assert result["version"] == "1.10.2"
        assert result["category"] == "System"
        assert result["description"] == "Hardware and OS metrics"
        assert result["readme"] == "Test README"
        assert result["build_date"] == "2024-02-13T10:30:00Z"

        # RPM availability (amd64 -> x86_64)
        assert "el9" in result["availability"]
        assert "x86_64" in result["availability"]["el9"]
        assert result["availability"]["el9"]["x86_64"]["status"] == "success"
        assert (
            result["availability"]["el9"]["x86_64"]["path"]
            == "https://test.com/node_exporter.rpm"
        )

        # DEB availability
        assert "ubuntu-22.04" in result["deb_availability"]
        assert "amd64" in result["deb_availability"]["ubuntu-22.04"]

        # Status fields
        assert result["rpm_status"] == "success"
        assert result["deb_status"] == "success"
        assert result["docker_status"] == "success"

    def test_convert_arch_mapping_rpm(self):
        """RPM should map amd64->x86_64, arm64->aarch64."""
        metadata = {
            "exporter": "test",
            "version": "1.0.0",
            "artifacts": {
                "rpm": {
                    "el9": {
                        "amd64": {"status": "success", "url": "url1"},
                        "arm64": {"status": "success", "url": "url2"},
                    }
                },
                "deb": {},
                "docker": {},
            },
            "status": {"rpm": "success", "deb": "na", "docker": "na"},
        }

        result = convert_metadata_to_legacy_format(metadata, {})

        # Check arch mapping
        assert "x86_64" in result["availability"]["el9"]
        assert "aarch64" in result["availability"]["el9"]
        assert "amd64" not in result["availability"]["el9"]
        assert "arm64" not in result["availability"]["el9"]

    def test_convert_no_metadata(self):
        """Null metadata should use manifest only."""
        manifest = {
            "name": "test_exporter",
            "version": "v1.0.0",
            "category": "Database",
            "description": "Test exporter",
            "readme": "Test README",
        }

        result = convert_metadata_to_legacy_format(None, manifest)

        assert result["name"] == "test_exporter"
        assert result["version"] == "1.0.0"  # v stripped
        assert result["category"] == "Database"
        assert result["build_date"] is None
        assert result["availability"] == {}
        assert result["deb_availability"] == {}
        assert result["rpm_status"] == "na"
        assert result["deb_status"] == "na"
        assert result["docker_status"] == "na"

    def test_convert_default_readme(self):
        """Missing README should use default message."""
        metadata = {
            "exporter": "test",
            "version": "1.0.0",
            "artifacts": {"rpm": {}, "deb": {}, "docker": {}},
            "status": {"rpm": "na", "deb": "na", "docker": "na"},
        }

        result = convert_metadata_to_legacy_format(metadata, {})

        assert result["readme"] == "No documentation available."

    def test_convert_empty_artifacts(self):
        """Empty artifacts should result in empty availability."""
        metadata = {
            "exporter": "test",
            "version": "1.0.0",
            "artifacts": {"rpm": {}, "deb": {}, "docker": {"status": "na"}},
            "status": {"rpm": "na", "deb": "na", "docker": "na"},
        }

        result = convert_metadata_to_legacy_format(metadata, {})

        assert result["availability"] == {}
        assert result["deb_availability"] == {}
        assert result["rpm_status"] == "na"
        assert result["deb_status"] == "na"

    def test_convert_preserves_status(self):
        """Status values should be preserved from V3."""
        metadata = {
            "exporter": "test",
            "version": "1.0.0",
            "artifacts": {"rpm": {}, "deb": {}, "docker": {}},
            "status": {
                "rpm": "failed",
                "deb": "pending",
                "docker": "success",
            },
        }

        result = convert_metadata_to_legacy_format(metadata, {})

        assert result["rpm_status"] == "failed"
        assert result["deb_status"] == "pending"
        assert result["docker_status"] == "success"
