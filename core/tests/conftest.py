"""
Pytest configuration and shared fixtures for the monitoring-hub test suite.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_manifest() -> dict[str, Any]:
    """Provide a valid sample manifest for testing."""
    return {
        "name": "test_exporter",
        "description": "Test exporter for unit tests",
        "version": "v1.0.0",
        "category": "System",
        "upstream": {"type": "github", "repo": "owner/test_exporter", "strategy": "latest_release"},
        "build": {
            "method": "binary_repack",
            "binary_name": "test_exporter",
            "archs": ["amd64", "arm64"],
        },
        "artifacts": {
            "rpm": {"enabled": True, "targets": ["el9"], "systemd": {"enabled": True}},
            "docker": {
                "enabled": True,
                "entrypoint": ["/usr/bin/test_exporter"],
                "validation": {"enabled": True, "port": 9100},
            },
        },
    }


@pytest.fixture
def sample_manifest_file(temp_dir: Path, sample_manifest: dict[str, Any]) -> Path:
    """Create a temporary manifest.yaml file."""
    manifest_path = temp_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(sample_manifest, f)
    return Path(manifest_path)


@pytest.fixture
def mock_exporter_dir(temp_dir: Path, sample_manifest: dict[str, Any]) -> Path:
    """Create a mock exporter directory structure."""
    exporter_dir = temp_dir / "exporters" / "test_exporter"
    exporter_dir.mkdir(parents=True)

    # Create manifest
    manifest_path = exporter_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(sample_manifest, f)

    # Create assets directory
    assets_dir = exporter_dir / "assets"
    assets_dir.mkdir()

    return Path(exporter_dir)


@pytest.fixture
def mock_catalog() -> dict[str, Any]:
    """Provide a mock catalog.json for state management tests."""
    return {
        "exporters": [
            {"name": "node_exporter", "version": "1.8.0", "description": "Hardware and OS metrics"},
            {"name": "prometheus", "version": "2.45.0", "description": "Prometheus server"},
        ]
    }


@pytest.fixture
def mock_github_release() -> dict[str, Any]:
    """Provide a mock GitHub release API response."""
    return {
        "tag_name": "v1.2.0",
        "name": "Release 1.2.0",
        "assets": [
            {
                "name": "test_exporter-1.2.0.linux-amd64.tar.gz",
                "browser_download_url": "https://example.com/download.tar.gz",
            }
        ],
    }


@pytest.fixture(autouse=True)
def set_pythonpath(monkeypatch, tmp_path):
    """Ensure PYTHONPATH is set correctly for imports."""
    project_root = Path(__file__).parent.parent.parent
    monkeypatch.setenv("PYTHONPATH", str(project_root))
