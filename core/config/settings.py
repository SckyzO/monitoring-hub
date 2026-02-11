# Monitoring Hub Configuration

# Supported Target Distributions
SUPPORTED_DISTROS = ["el8", "el9", "el10"]
SUPPORTED_DEB_DISTROS = ["ubuntu-22.04", "ubuntu-24.04", "debian-12", "debian-13"]

# DEB Distribution Codenames
DEB_CODENAME_MAP = {
    "ubuntu-22.04": "jammy",
    "ubuntu-24.04": "noble",
    "debian-12": "bookworm",
    "debian-13": "trixie",
}

# DEB Build Images
DEB_BUILD_IMAGES = {
    "ubuntu-22.04": "ubuntu:22.04",
    "ubuntu-24.04": "ubuntu:24.04",
    "debian-12": "debian:12",
    "debian-13": "debian:trixie",
}

# Architecture Mapping (Docker/Go -> RPM)
ARCH_MAP = {"amd64": "x86_64", "arm64": "aarch64"}

# Docker Defaults
DEFAULT_BASE_IMAGE = "registry.access.redhat.com/ubi9/ubi-minimal"

# Site & Catalog
DEFAULT_CATALOG_URL = "https://sckyzo.github.io/monitoring-hub/catalog/index.json"
REPO_ROOT_URL = "https://sckyzo.github.io/monitoring-hub"

# Paths (relative to project root)
TEMPLATES_DIR = "core/templates"
EXPORTERS_DIR = "exporters"
BUILD_DIR = "build"

# Versioning

CORE_VERSION = "v0.18.0"

PORTAL_VERSION = "v2.9.0"
