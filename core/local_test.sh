#!/bin/bash
set -e

# Usage: ./core/local_test.sh <exporter_name> [arch] [distro_image] [--smoke]
# Example: ./core/local_test.sh node_exporter amd64 almalinux:9 --smoke

EXPORTER=$1
ARCH=${2:-amd64}
# Check if argument 2 starts with -, if so, shift args
if [[ "$ARCH" == -* ]]; then
    ARCH="amd64"
fi

DISTRO=${3:-almalinux:9}
if [[ "$DISTRO" == -* ]]; then
    DISTRO="almalinux:9"
fi

# Simple argument parsing for flags
RUN_SMOKE=false
for arg in "$@"; do
    if [ "$arg" == "--smoke" ] || [ "$arg" == "-s" ]; then
        RUN_SMOKE=true
    fi
done

if [ -z "$EXPORTER" ]; then
    echo "Usage: $0 <exporter_name> [arch] [distro_image] [--smoke]"
    echo "Example: $0 node_exporter --smoke"
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

# 5. Smoke Test (Validation)
if [ "$RUN_SMOKE" = true ]; then
    echo "------------------------------------------------"
    echo ">> [4/3] Running Smoke Tests..."

    # Extract validation config using python
    VAL_CONFIG=$(python3 -c "
import yaml
try:
    with open('exporters/$EXPORTER/manifest.yaml', 'r') as f:
        data = yaml.safe_load(f)
        val = data.get('artifacts', {}).get('docker', {}).get('validation', {})
        enabled = val.get('enabled', True)
        port = val.get('port', 'None')
        cmd = val.get('command', 'None')
        print(f'{enabled}|{port}|{cmd}')
except Exception as e:
    print('True|None|None')
")

    IFS='|' read -r V_ENABLED V_PORT V_CMD <<< "$VAL_CONFIG"

    if [ "$V_ENABLED" != "True" ]; then
        echo "Creating smoke test skipped (disabled in manifest)."
    else
        IMAGE_ID="monitoring-hub/$EXPORTER:local"
        
        # Command Validation
        if [ "$V_CMD" != "None" ]; then
            echo "🚀 Validating with command: $V_CMD"
            if docker run --rm "$IMAGE_ID" $V_CMD; then
                echo "✅ Command validation PASSED!"
            else
                echo "❌ Command validation FAILED!"
                exit 1
            fi
        fi

        # Port Validation
        if [ "$V_PORT" != "None" ]; then
            echo "🚀 Validating on port $V_PORT..."
            CONTAINER_ID=$(docker run -d -p 9999:$V_PORT "$IMAGE_ID")
            
            # Give it a moment to start
            sleep 2
            
            SUCCESS=false
            for i in {1..5}; do
                echo "Attempt $i: Checking http://localhost:9999/metrics..."
                if curl -s --fail "http://localhost:9999/metrics" | grep -qiE "prometheus|exporter|metrics|# HELP|# TYPE" >/dev/null; then
                    echo "✅ Port validation PASSED!"
                    SUCCESS=true
                    break
                fi
                sleep 2
            done
            
            docker rm -f $CONTAINER_ID >/dev/null
            
            if [ "$SUCCESS" = false ]; then
                echo "❌ Port validation FAILED!"
                exit 1
            fi
        fi
        
        if [ "$V_CMD" == "None" ] && [ "$V_PORT" == "None" ]; then
             echo "⚠️ No specific validation configured (port or command), but build succeeded."
        fi
    fi
fi

echo "------------------------------------------------"
echo "✅ SUCCESS: All local tests passed for $EXPORTER."
echo "   RPM: build/$EXPORTER/rpms"
echo "   Docker: monitoring-hub/$EXPORTER:local"
