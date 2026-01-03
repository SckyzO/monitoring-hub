#!/bin/bash
set -e

# Usage: ./core/local_test.sh <exporter_name> [arch] [distro_image]
# Example: ./core/local_test.sh node_exporter amd64 almalinux:9

EXPORTER=$1
ARCH=${2:-amd64}
DISTRO=${3:-almalinux:9}

if [ -z "$EXPORTER" ]; then
    echo "Usage: $0 <exporter_name> [arch] [distro_image]"
    echo "Example: $0 node_exporter"
    exit 1
fi

PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

# 1. Activate venv if exists
if [ -f .venv/bin/activate ]; then
    echo ">> Activating virtual environment..."
    source .venv/bin/activate
fi

# 2. Generate Build Files
echo "------------------------------------------------"
echo ">> [1/3] Generating build files for $EXPORTER ($ARCH)..."
python3 core/builder.py --manifest "exporters/$EXPORTER/manifest.yaml" --arch "$ARCH" --output-dir "build/$EXPORTER"

# 3. Build RPM
echo "------------------------------------------------"
echo ">> [2/3] Building RPM using $DISTRO..."
./core/build_rpm.sh "build/$EXPORTER/$EXPORTER.spec" "build/$EXPORTER/rpms" "$ARCH" "$DISTRO"

# 4. Build Docker Image
echo "------------------------------------------------"
echo ">> [3/3] Building Docker image..."
docker build -t "monitoring-hub/$EXPORTER:local" "build/$EXPORTER"

echo "------------------------------------------------"
echo "✅ SUCCESS: All local tests passed for $EXPORTER."
echo "   RPM: build/$EXPORTER/rpms"
echo "   Docker: monitoring-hub/$EXPORTER:local"
