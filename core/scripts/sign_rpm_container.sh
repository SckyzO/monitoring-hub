#!/bin/bash
# Sign an RPM package with GPG key inside a Docker container
# Usage: sign_rpm_container.sh <rpm_file> <gpg_key_base64> <passphrase> <key_id>

set -euo pipefail

if [ $# -lt 4 ]; then
    echo "Usage: $0 <rpm_file> <gpg_key_base64> <passphrase> <key_id>"
    exit 1
fi

RPM_FILE="$1"
GPG_KEY_BASE64="$2"
GPG_PASSPHRASE="$3"
GPG_KEY_ID="$4"

if [ ! -f "$RPM_FILE" ]; then
    echo "Error: RPM file not found: $RPM_FILE"
    exit 1
fi

# Get absolute paths
RPM_FILE_ABS=$(readlink -f "$RPM_FILE")
RPM_DIR=$(dirname "$RPM_FILE_ABS")
RPM_NAME=$(basename "$RPM_FILE_ABS")

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect RHEL version from RPM filename (e.g., .el9, .el10)
RHEL_VERSION="9"  # Default
if [[ "$RPM_NAME" =~ \.el([0-9]+)\. ]]; then
    RHEL_VERSION="${BASH_REMATCH[1]}"
fi

CONTAINER_IMAGE="almalinux:${RHEL_VERSION}"

echo "=== Signing RPM in Docker container ==="
echo "RPM: $RPM_NAME"
echo "Detected RHEL version: el${RHEL_VERSION}"
echo "Container image: $CONTAINER_IMAGE"
echo ""

# Run signing in Docker container
docker run --rm \
    -v "$RPM_DIR:/rpms:rw" \
    -v "$SCRIPT_DIR:/scripts:ro" \
    -e "GPG_KEY_BASE64=$GPG_KEY_BASE64" \
    -e "GPG_PASSPHRASE=$GPG_PASSPHRASE" \
    -e "GPG_KEY_ID=$GPG_KEY_ID" \
    "$CONTAINER_IMAGE" \
    bash -c "
        set -euo pipefail

        # Install required packages
        echo '==> Installing rpm-sign and gnupg...'
        dnf install -y -q rpm-sign gnupg2 > /dev/null 2>&1

        # Copy RPM to writable location
        cp /rpms/$RPM_NAME /tmp/$RPM_NAME
        chmod 644 /tmp/$RPM_NAME

        # Run signing script
        /scripts/sign_rpm.sh /tmp/$RPM_NAME \"\$GPG_KEY_BASE64\" \"\$GPG_PASSPHRASE\" \"\$GPG_KEY_ID\"

        # Copy signed RPM back
        cp /tmp/$RPM_NAME /rpms/$RPM_NAME

        echo ''
        echo '✓ RPM signed successfully in container'
    "

echo ""
echo "✓ RPM signed and saved to: $RPM_FILE"
