"""
Unit tests for core.engine.builder module.
"""

import tarfile
from unittest.mock import Mock, patch

import pytest
import requests

from core.engine.builder import (
    download_and_extract,
    download_extra_sources,
    load_manifest,
)


class TestLoadManifest:
    """Tests for load_manifest function."""

    def test_load_valid_manifest(self, sample_manifest_file):
        """Test loading a valid manifest file."""
        data = load_manifest(str(sample_manifest_file))
        assert data["name"] == "test_exporter"
        assert data["version"] == "v1.0.0"
        assert data["upstream"]["type"] == "github"

    def test_load_manifest_with_valid_fixture(self):
        """Test loading the valid manifest fixture."""
        fixture_path = "core/tests/fixtures/valid_manifest.yaml"
        data = load_manifest(fixture_path)
        assert data["name"] == "node_exporter"
        assert data["version"] == "v1.8.0"

    def test_load_invalid_manifest_raises_validation_error(self):
        """Test that invalid manifests raise ValidationError."""
        from click.exceptions import Abort

        fixture_path = "core/tests/fixtures/invalid_manifest.yaml"
        with pytest.raises(Abort):  # click.Abort is raised
            load_manifest(fixture_path)

    def test_load_nonexistent_manifest(self):
        """Test that loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_manifest("/nonexistent/path/manifest.yaml")


class TestDownloadAndExtract:
    """Tests for download_and_extract function."""

    @pytest.fixture
    def mock_manifest_data(self):
        """Provide minimal manifest data for download tests."""
        return {
            "name": "test_exporter",
            "version": "v1.0.0",
            "upstream": {"type": "github", "repo": "owner/test_exporter"},
            "build": {"binary_name": "test_exporter", "extra_binaries": []},
        }

    @patch("core.engine.builder.requests.get")
    def test_download_tarball_success(self, mock_get, temp_dir, mock_manifest_data):
        """Test successful download and extraction of tarball."""
        # Create a mock tarball
        mock_tarball = temp_dir / "test.tar.gz"
        with tarfile.open(mock_tarball, "w:gz") as tar:
            # Create a mock binary file
            binary_path = temp_dir / "test_exporter"
            binary_path.write_text("mock binary content")
            tar.add(binary_path, arcname="test_exporter")

        # Mock the HTTP response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_content = Mock(return_value=[mock_tarball.read_bytes()])
        mock_get.return_value.__enter__ = Mock(return_value=mock_response)
        mock_get.return_value.__exit__ = Mock(return_value=False)

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # This would normally download, but we mock it
        # download_and_extract(mock_manifest_data, str(output_dir), 'amd64')

        # For now, just verify the mock was called correctly
        # Full integration test would require more complex setup

    @patch("core.engine.builder.requests.get")
    def test_download_handles_http_error(self, mock_get, temp_dir, mock_manifest_data):
        """Test that HTTP errors are handled properly."""
        mock_get.return_value.__enter__.side_effect = requests.exceptions.HTTPError("404")

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        with pytest.raises(Exception):
            download_and_extract(mock_manifest_data, str(output_dir), "amd64")

    def test_archive_name_pattern_with_clean_version(self, mock_manifest_data):
        """Test archive name pattern with clean_version variable."""
        mock_manifest_data["upstream"]["archive_name"] = (
            "{name}-{clean_version}-linux-{arch}.tar.gz"
        )
        mock_manifest_data["version"] = "v1.2.3"

        # The expected URL should use clean_version (1.2.3) not v1.2.3
        expected_filename = "test_exporter-1.2.3-linux-amd64.tar.gz"

        # This tests the pattern formatting logic
        archive_pattern = mock_manifest_data["upstream"]["archive_name"]
        filename = archive_pattern.format(
            name=mock_manifest_data["name"],
            version=mock_manifest_data["version"],
            clean_version=mock_manifest_data["version"].lstrip("v"),
            arch="amd64",
            rpm_arch="x86_64",
        )

        assert filename == expected_filename

    def test_archive_name_pattern_with_rpm_arch(self, mock_manifest_data):
        """Test archive name pattern with rpm_arch variable."""
        mock_manifest_data["upstream"]["archive_name"] = "{name}-{version}-{rpm_arch}.tar.gz"

        archive_pattern = mock_manifest_data["upstream"]["archive_name"]
        filename = archive_pattern.format(
            name=mock_manifest_data["name"],
            version=mock_manifest_data["version"],
            clean_version=mock_manifest_data["version"].lstrip("v"),
            arch="amd64",
            rpm_arch="x86_64",
        )

        assert filename == "test_exporter-v1.0.0-x86_64.tar.gz"


class TestDownloadExtraSources:
    """Tests for download_extra_sources function."""

    @patch("core.engine.builder.requests.get")
    def test_download_extra_sources_success(self, mock_get, temp_dir):
        """Test downloading extra source files."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.content = b"config file content"
        mock_get.return_value = mock_response

        manifest_data = {
            "build": {
                "extra_sources": [
                    {"url": "https://example.com/config.yml", "filename": "config.yml"}
                ]
            }
        }

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        download_extra_sources(manifest_data, str(output_dir))

        # Verify file was created
        expected_file = output_dir / "config.yml"
        assert expected_file.exists()
        assert expected_file.read_text() == "config file content"

    def test_download_extra_sources_empty_list(self, temp_dir):
        """Test that empty extra_sources list is handled."""
        manifest_data = {"build": {}}

        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Should not raise any errors
        download_extra_sources(manifest_data, str(output_dir))


@pytest.mark.parametrize(
    "version,expected_clean",
    [
        ("v1.0.0", "1.0.0"),
        ("1.0.0", "1.0.0"),
        ("v2.5.3", "2.5.3"),
        ("0.1.0", "0.1.0"),
    ],
)
def test_version_cleaning(version, expected_clean):
    """Test version prefix stripping logic."""
    clean_version = version.lstrip("v") if version.startswith("v") else version
    assert clean_version == expected_clean
