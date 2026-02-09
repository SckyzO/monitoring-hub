# Quick Start

Get up and running with Monitoring Hub in just a few minutes.

## For Users (Installing Exporters)

### 1. Configure Repository

```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/
```

### 2. Install Exporter

```bash
sudo dnf install node_exporter
```

### 3. Start Service

```bash
sudo systemctl enable --now node_exporter
```

### 4. Verify

```bash
curl http://localhost:9100/metrics
```

Done! The exporter is running and exposing metrics.

## For Contributors (Adding Exporters)

### 1. Clone Repository

```bash
git clone https://github.com/SckyzO/monitoring-hub.git
cd monitoring-hub
```

### 2. Build Development Environment

**No Python installation required - just Docker!**

```bash
./devctl build
```

This creates a Docker image with all development tools pre-installed.

### 3. Create Exporter

```bash
./devctl create-exporter
```

Follow the interactive prompts:

- **Name:** `my_exporter`
- **Repo:** `owner/my_exporter`
- **Category:** Select appropriate category
- **Description:** Short description

### 4. Test Locally

```bash
./devctl test-exporter my_exporter
```

This will build RPM + Docker image and run validation tests.

### 5. Commit and Push

```bash
git checkout -b feature/add-my-exporter
git add exporters/my_exporter/
git commit -m "feat(exporters): add my_exporter"
git push origin feature/add-my-exporter
```

### 6. Create Pull Request

Open a PR on GitHub. CI will automatically:

- Validate the manifest
- Build RPM packages
- Build Docker images
- Run validation tests

Once approved and merged, your exporter will be automatically deployed!

## What's Next?

- **Users:** [Installation Guide](installation.md) for more installation options
- **Contributors:** [Adding Exporters](../user-guide/adding-exporters.md) for detailed guide
- **Developers:** [Development Setup](../contributing/development.md) for setting up dev environment
