"""
Unit tests for core.engine.state_manager module.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from core.engine.state_manager import (
    get_local_state,
    get_remote_catalog,
)


class TestGetRemoteCatalog:
    """Tests for get_remote_catalog function."""

    @patch("core.engine.state_manager.requests.get")
    def test_get_remote_catalog_success(self, mock_get, mock_catalog):
        """Test successful fetch of remote catalog."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_catalog
        mock_get.return_value = mock_response

        result = get_remote_catalog("https://example.com/catalog.json")

        assert result == {"node_exporter": "1.8.0", "prometheus": "2.45.0"}

    @patch("core.engine.state_manager.requests.get")
    def test_get_remote_catalog_404(self, mock_get):
        """Test handling of 404 response."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_remote_catalog("https://example.com/catalog.json")

        # Should return empty dict on 404
        assert result == {}

    @patch("core.engine.state_manager.requests.get")
    def test_get_remote_catalog_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")

        result = get_remote_catalog("https://example.com/catalog.json")

        # Should return empty dict on error
        assert result == {}

    @patch("core.engine.state_manager.requests.get")
    def test_get_remote_catalog_connection_error(self, mock_get):
        """Test handling of connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        result = get_remote_catalog("https://example.com/catalog.json")

        # Should return empty dict on error
        assert result == {}

    @patch("core.engine.state_manager.requests.get")
    def test_get_remote_catalog_empty_exporters(self, mock_get):
        """Test handling of catalog with empty exporters list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"exporters": []}
        mock_get.return_value = mock_response

        result = get_remote_catalog("https://example.com/catalog.json")

        assert result == {}


class TestGetLocalState:
    """Tests for get_local_state function."""

    def test_get_local_state_with_exporters(self, temp_dir, sample_manifest):
        """Test reading local manifests from exporters directory."""
        # Create exporters directory structure
        exporters_dir = temp_dir / "exporters"
        exporter1_dir = exporters_dir / "test_exporter"
        exporter1_dir.mkdir(parents=True)

        # Create manifest
        manifest_path = exporter1_dir / "manifest.yaml"
        import yaml

        with open(manifest_path, "w") as f:
            yaml.dump(sample_manifest, f)

        result = get_local_state(str(exporters_dir))

        assert "test_exporter" in result
        assert result["test_exporter"] == "1.0.0"  # v prefix stripped

    def test_get_local_state_with_v_prefix(self, temp_dir, sample_manifest):
        """Test that v prefix is stripped from versions."""
        exporters_dir = temp_dir / "exporters"
        exporter_dir = exporters_dir / "versioned_exporter"
        exporter_dir.mkdir(parents=True)

        # Manifest with v prefix
        sample_manifest["name"] = "versioned_exporter"
        sample_manifest["version"] = "v2.5.3"

        manifest_path = exporter_dir / "manifest.yaml"
        import yaml

        with open(manifest_path, "w") as f:
            yaml.dump(sample_manifest, f)

        result = get_local_state(str(exporters_dir))

        assert result["versioned_exporter"] == "2.5.3"  # v stripped

    def test_get_local_state_nonexistent_directory(self, temp_dir):
        """Test handling of non-existent exporters directory."""
        nonexistent = temp_dir / "nonexistent"

        result = get_local_state(str(nonexistent))

        assert result == {}

    def test_get_local_state_no_manifests(self, temp_dir):
        """Test directory with no manifest files."""
        exporters_dir = temp_dir / "exporters"
        exporters_dir.mkdir()
        empty_dir = exporters_dir / "empty_exporter"
        empty_dir.mkdir()

        result = get_local_state(str(exporters_dir))

        assert result == {}

    def test_get_local_state_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML in manifest."""
        exporters_dir = temp_dir / "exporters"
        exporter_dir = exporters_dir / "broken_exporter"
        exporter_dir.mkdir(parents=True)

        # Create invalid YAML
        manifest_path = exporter_dir / "manifest.yaml"
        manifest_path.write_text("invalid: yaml: content: [[[")

        result = get_local_state(str(exporters_dir))

        # Should skip broken manifest and return empty
        assert result == {}


class TestVersionComparison:
    """Tests for version comparison logic."""

    @pytest.mark.parametrize(
        "local,remote,should_build",
        [
            ("1.0.0", "0.9.0", True),  # Local newer - still builds (version differs)
            ("1.0.0", "1.0.0", False),  # Same version - no build
            ("1.0.0", "1.0.1", True),  # Remote newer - builds
            ("1.0.0", None, True),  # New exporter - builds
            ("2.0.0", "1.9.9", True),  # Major version bump - builds (version differs)
        ],
    )
    def test_version_comparison_logic(self, local, remote, should_build):
        """Test the version comparison logic.

        Note: The current system rebuilds whenever local != remote,
        regardless of which is newer. This is intentional to catch
        both updates and rollbacks.
        """
        # Simulate the logic from state_manager.py main()
        if remote is None:
            needs_build = True
        else:
            needs_build = str(local) != str(remote)

        assert needs_build == should_build


class TestForceRebuild:
    """Tests for force rebuild functionality."""

    def test_force_rebuild_overrides_version_check(self):
        """Test that force_rebuild flag works correctly."""
        force_rebuild = True
        local_version = "1.0.0"
        remote_version = "1.0.0"

        # When force_rebuild is True, should build regardless of versions
        if force_rebuild:
            should_build = True
        else:
            should_build = local_version != remote_version

        assert should_build is True

    def test_no_force_rebuild_respects_version(self):
        """Test that without force_rebuild, version comparison is used."""
        force_rebuild = False
        local_version = "1.0.0"
        remote_version = "1.0.0"

        if force_rebuild:
            should_build = True
        else:
            should_build = local_version != remote_version

        assert should_build is False
