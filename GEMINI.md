# Monitoring Hub

**Monitoring Hub** is a "Software Factory" designed to automate the production of production-ready Prometheus Exporters. It transforms high-level YAML manifests into standard artifacts: **RPM packages** (for Enterprise Linux 8, 9, 10) and **Docker images** (based on UBI 9 Minimal).

## 📂 Project Structure

*   `core/`: The engine room. Contains the Python build logic, Jinja2 templates, and helper scripts.
    *   `engine/`: Core Python modules (`builder.py`, `site_generator.py`).
    *   `scripts/`: Shell and Python scripts for CLI operations (`create_exporter.py`, `local_test.sh`).
    *   `templates/`: Default Jinja2 templates for `.spec` files and `Dockerfiles`.
*   `exporters/`: The registry of supported tools. Each folder matches an exporter name (e.g., `node_exporter`).
    *   `manifest.yaml`: The single source of truth for the exporter's configuration.
    *   `assets/`: Config files, scripts, or extra binaries needed for the build.
    *   `templates/`: (Optional) Overrides for default templates (e.g., custom `Dockerfile.j2`).
*   `.github/`: CI/CD workflows and assets.

## 🛠 Tech Stack

*   **Language:** Python 3.9+ (Build Engine), Bash (Glue).
*   **Templating:** Jinja2 (for generating RPM Spec files and Dockerfiles).
*   **Packaging:** RPM (via `rpmbuild`), Docker (via `docker build`).
*   **Base Image:** Red Hat UBI 9 Minimal (Hardened, Small).
*   **Validation:** `local_test.sh` runs containerized smoke tests (port checks, command validation).

## 🚀 Key Commands

### 1. Create a New Exporter
Scaffolds a new directory in `exporters/` with a standard manifest and README.

```bash
./core/scripts/create_exporter.py --name my_exporter --repo owner/repo --category System
```

### 2. Local Integration Test (Recommended)
Runs the full pipeline: generates build files, builds the RPM (in Docker), builds the Docker image, and runs validation tests.

```bash
# Build and test node_exporter (RPM EL9 + Docker + Validation)
./core/scripts/local_test.sh node_exporter --validate

# Build only RPM for EL8
./core/scripts/local_test.sh node_exporter --el8
```

### 3. Manual Build (Debug)
If you need to debug the generation phase specifically:

```bash
export PYTHONPATH=$(pwd)
python3 -m core.engine.builder --manifest exporters/node_exporter/manifest.yaml --output-dir build/debug
```

## 📝 Development Conventions

*   **Manifest First:** All logic should be driven by `manifest.yaml`. Avoid hardcoding logic in scripts if it can be defined in the manifest.
*   **Reference Schema:** Always consult `manifest.reference.yaml` when adding new features or fields to manifests.
*   **Canary Testing:** `node_exporter` is used as the "Canary" in CI (`.github/workflows/build-pr.yml`). If you break `node_exporter`, you break the build.
*   **Validation:** Every exporter SHOULD have a `validation` section in its manifest to ensure the generated container actually starts and serves metrics.
*   **Cleanliness:** Python dependencies are in `core/requirements.txt`. Use a venv.

## 📦 Artifacts

Build outputs are stored in `build/<exporter_name>/`:
*   `*.spec`: Generated RPM Spec file.
*   `Dockerfile`: Generated Dockerfile.
*   `rpms/`: Directory containing built RPMs.
