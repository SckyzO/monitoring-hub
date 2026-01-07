#!/bin/bash
set -e

# --- Configuration ---
HOST_PORT=${HOST_PORT:-9999}
PROJECT_ROOT=$(git rev-parse --show-toplevel)

# --- Colors ---
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# --- State ---
EXPORTER=""
ARCH="amd64"
DO_RPM_EL8=false
DO_RPM_EL9=false
DO_RPM_EL10=false
DO_DOCKER=false
DO_VALIDATE=false
VERBOSE=false
DEFAULT_MODE=true

declare -A RESULTS

# --- Functions ---

usage() {
    echo "Usage: $0 <exporter_name> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --el8        Build RPM for Enterprise Linux 8"
    echo "  --el9        Build RPM for Enterprise Linux 9"
    echo "  --el10       Build RPM for Enterprise Linux 10"
    echo "  --docker     Build Docker image"
    echo "  --validate   Run port/command validation tests"
    echo "  --arch       Target architecture (default: amd64)"
    echo "  --port       Host port for validation (default: 9999)"
    echo "  --verbose    Show verbose output for builds"
    echo ""
    echo "Default behavior (if no build flags): Builds EL9 RPM + Docker"
}

log_info() { echo -e "${BLUE}$1${RESET}"; }
log_success() { echo -e "${GREEN}$1${RESET}"; }
log_warn() { echo -e "${YELLOW}$1${RESET}"; }
log_error() { echo -e "${RED}$1${RESET}"; }

run_cmd() {
    local cmd="$@"
    if [ "$VERBOSE" = true ]; then
        eval "$cmd"
    else
        eval "$cmd" > /dev/null 2>&1
    fi
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --el8)      DO_RPM_EL8=true; DEFAULT_MODE=false; shift ;;
            --el9)      DO_RPM_EL9=true; DEFAULT_MODE=false; shift ;;
            --el10)     DO_RPM_EL10=true; DEFAULT_MODE=false; shift ;;
            --docker)   DO_DOCKER=true; DEFAULT_MODE=false; shift ;;
            --validate|--check|--smoke) DO_VALIDATE=true; shift ;;
            --arch)     ARCH="$2"; shift; shift ;;
            --port)     HOST_PORT="$2"; shift; shift ;;
            --verbose)  VERBOSE=true; shift ;;
            -h|--help)  usage; exit 0 ;;
            *)
                if [ -z "$EXPORTER" ]; then
                    EXPORTER=$1
                else
                    log_error "Unknown argument: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [ -z "$EXPORTER" ]; then
        log_error "Error: Exporter name required."
        usage
        exit 1
    fi

    if [ "$DEFAULT_MODE" = true ]; then
        DO_RPM_EL9=true
        DO_DOCKER=true
    fi
}

setup_env() {
    cd "$PROJECT_ROOT"
    if [ -f .venv/bin/activate ]; then
        if [ "$VERBOSE" = true ]; then
            log_info ">> Activating virtual environment..."
        fi
        source .venv/bin/activate
    fi
}

generate_build_files() {
    echo "------------------------------------------------"
    log_info "🔨 [1/X] Generating build files for ${BOLD}$EXPORTER${RESET}${BLUE} ($ARCH)..."
    export PYTHONPATH="$PROJECT_ROOT"
    
    if [ "$VERBOSE" = true ]; then
        python3 -m core.engine.builder --manifest "exporters/$EXPORTER/manifest.yaml" --arch "$ARCH" --output-dir "build/$EXPORTER"
    else
        python3 -m core.engine.builder --manifest "exporters/$EXPORTER/manifest.yaml" --arch "$ARCH" --output-dir "build/$EXPORTER" > /dev/null 2>&1
    fi

    if [ $? -eq 0 ]; then
        RESULTS[SETUP]="✅ OK"
    else
        RESULTS[SETUP]="❌ FAIL"
        log_error "Failed to generate build files. Run with --verbose for details."
        exit 1
    fi
}

build_rpm() {
    local dist_name=$1
    local dist_image=$2
    
    echo "------------------------------------------------"
    log_info "📦 Building RPM for ${BOLD}$dist_name${RESET}${BLUE}..."
    
    mkdir -p "build/$EXPORTER/rpms/$dist_name"
    
    if [ "$VERBOSE" = true ]; then
        ./core/scripts/build_rpm.sh "build/$EXPORTER/$EXPORTER.spec" "build/$EXPORTER/rpms/$dist_name" "$ARCH" "$dist_image"
    else
        ./core/scripts/build_rpm.sh "build/$EXPORTER/$EXPORTER.spec" "build/$EXPORTER/rpms/$dist_name" "$ARCH" "$dist_image" > /dev/null 2>&1
    fi

    if [ $? -eq 0 ]; then
        RESULTS["RPM $dist_name"]="✅ OK"
    else
        RESULTS["RPM $dist_name"]="❌ FAIL"
        log_error "RPM build failed for $dist_name. Run with --verbose for details."
        exit 1
    fi
}

build_docker() {
    echo "------------------------------------------------"
    log_info "🐳 Building Docker image..."
    
    local build_cmd="docker build -t monitoring-hub/$EXPORTER:local build/$EXPORTER"
    
    if [ "$VERBOSE" = true ]; then
        $build_cmd
    else
        $build_cmd > /dev/null 2>&1
    fi

    if [ $? -eq 0 ]; then
        RESULTS["Docker Build"]="✅ OK"
    else
        RESULTS["Docker Build"]="❌ FAIL"
        log_error "Docker build failed. Run with --verbose for details."
        exit 1
    fi
}

run_validation() {
    echo "------------------------------------------------"
    log_info "🔍 Running Validation Tests..."

    # Extract validation config from manifest using Python
    VAL_CONFIG=$(export PYTHONPATH="$PROJECT_ROOT"; python3 -c "
import yaml
try:
    with open('exporters/$EXPORTER/manifest.yaml', 'r') as f:
        data = yaml.safe_load(f)
        val = data.get('artifacts', {}).get('docker', {}).get('validation', {})
        enabled = val.get('enabled', True)
        port = val.get('port', 'None')
        cmd = val.get('command', 'None')
        args = val.get('args', 'None')
        print(f'{enabled}|{port}|{cmd}|{args}')
except Exception as e:
    print('True|None|None|None')
")

    IFS='|' read -r V_ENABLED V_PORT V_CMD V_ARGS <<< "$VAL_CONFIG"

    if [ "$V_ENABLED" != "True" ]; then
        echo "Validation disabled in manifest."
        RESULTS["Validation"]="⏭️ SKIPPED"
        return
    fi

    IMAGE_ID="monitoring-hub/$EXPORTER:local"
    VALIDATION_PASSED=true
    
    # 1. Command Validation (One-shot command)
    if [ "$V_CMD" != "None" ]; then
        echo "   🚀 Checking command: $V_CMD"
        if docker run --rm "$IMAGE_ID" $V_CMD > /dev/null 2>&1; then
            log_success "   ✅ Command check passed"
        else
            log_error "   ❌ Command check failed"
            VALIDATION_PASSED=false
        fi
    fi

    # 2. Port Validation (Server mode)
    if [ "$V_PORT" != "None" ]; then
        echo "   🚀 Checking port metrics: $V_PORT (mapped to localhost:$HOST_PORT)..."
        
        # Ensure cleanup of previous container on same port
        docker rm -f "test-${EXPORTER}" >/dev/null 2>&1 || true

        # Prepare run command with optional args
        RUN_ARGS=""
        if [ "$V_ARGS" != "None" ]; then
            RUN_ARGS="$V_ARGS"
            echo "      With arguments: $RUN_ARGS"
        fi

        # Start container detached
        CONTAINER_ID=$(docker run -d --name "test-${EXPORTER}" -p $HOST_PORT:$V_PORT "$IMAGE_ID" $RUN_ARGS)
        
        # Give container time to initialize
        sleep 3
        
        # Check if container is still running
        if ! docker ps -q -f id=$CONTAINER_ID >/dev/null; then
             log_error "   ❌ Container died immediately. Logs:"
             docker logs $CONTAINER_ID
             VALIDATION_PASSED=false
        else
            PORT_SUCCESS=false
            for i in {1..5}; do
                if curl -s --fail "http://localhost:$HOST_PORT/metrics" | grep -qiE "prometheus|exporter|metrics|# HELP|# TYPE" >/dev/null;
 then
                    PORT_SUCCESS=true
                    break
                fi
                sleep 2
            done
            
            if [ "$PORT_SUCCESS" = true ]; then
                log_success "   ✅ Metrics check passed"
            else
                log_error "   ❌ Metrics check failed (timeout or invalid response)"
                echo "      Last container logs:"
                docker logs $CONTAINER_ID | tail -n 5
                VALIDATION_PASSED=false
            fi
        fi
        
        docker rm -f $CONTAINER_ID >/dev/null
    fi
    
    if [ "$VALIDATION_PASSED" = true ]; then
        RESULTS["Validation"]="✅ PASS"
    else
        RESULTS["Validation"]="❌ FAIL"
        exit 1
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${BOLD}📊 Test Summary for ${CYAN}$EXPORTER${RESET}"
    echo "=========================================="
    for key in "${!RESULTS[@]}"; do
        printf "% -20s %b\n" "$key" "${RESULTS[$key]}"
    done
    echo "=========================================="
    echo ""

    if [ "$DO_DOCKER" = true ]; then
        echo -e "🐳 Image: ${YELLOW}monitoring-hub/$EXPORTER:local${RESET}"
    fi
    echo ""
}

# --- Main Execution ---

parse_args "$@"
setup_env
RESULTS[SETUP]="PENDING"

generate_build_files

if [ "$DO_RPM_EL8" = true ]; then build_rpm "el8" "almalinux:8"; fi
if [ "$DO_RPM_EL9" = true ]; then build_rpm "el9" "almalinux:9"; fi
if [ "$DO_RPM_EL10" = true ]; then build_rpm "el10" "almalinux:10"; fi

if [ "$DO_DOCKER" = true ]; then
    build_docker
    if [ "$DO_VALIDATE" = true ]; then
        run_validation
    fi
fi

print_summary
