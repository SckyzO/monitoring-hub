# Monitoring Hub Configuration

# Supported Target Distributions
SUPPORTED_DISTROS = ["el8", "el9", "el10"]

# Architecture Mapping (Docker/Go -> RPM)
ARCH_MAP = {"amd64": "x86_64", "arm64": "aarch64"}

# Docker Defaults
DEFAULT_BASE_IMAGE = "registry.access.redhat.com/ubi9/ubi-minimal"

# Site & Catalog
DEFAULT_CATALOG_URL = "https://sckyzo.github.io/monitoring-hub/catalog.json"
REPO_ROOT_URL = "https://sckyzo.github.io/monitoring-hub"

# Paths (relative to project root)
TEMPLATES_DIR = "core/templates"
EXPORTERS_DIR = "exporters"
BUILD_DIR = "build"

# Versioning

CORE_VERSION = "v0.17.0"

PORTAL_VERSION = "v2.8.0"
