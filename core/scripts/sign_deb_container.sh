#!/bin/bash
# Sign a DEB package with GPG key inside a Docker container
# Usage: sign_deb_container.sh <deb_file> <gpg_key_base64> <passphrase> <key_id> [distro]

set -euo pipefail

if [ $# -lt 4 ]; then
    echo "Usage: $0 <deb_file> <gpg_key_base64> <passphrase> <key_id> [distro]"
    echo ""
    echo "Optional distro: ubuntu-22.04, ubuntu-24.04, debian-12, debian-13"
    echo "Default: debian-12"
    exit 1
fi

DEB_FILE="$1"
GPG_KEY_BASE64="$2"
GPG_PASSPHRASE="$3"
GPG_KEY_ID="$4"
DISTRO="${5:-debian-12}"

if [ ! -f "$DEB_FILE" ]; then
    echo "Error: DEB file not found: $DEB_FILE"
    exit 1
fi

# Get absolute paths
DEB_FILE_ABS=$(readlink -f "$DEB_FILE")
DEB_DIR=$(dirname "$DEB_FILE_ABS")
DEB_NAME=$(basename "$DEB_FILE_ABS")

# Map distribution to Docker image
case "$DISTRO" in
    ubuntu-22.04)
        CONTAINER_IMAGE="ubuntu:22.04"
        ;;
    ubuntu-24.04)
        CONTAINER_IMAGE="ubuntu:24.04"
        ;;
    debian-12)
        CONTAINER_IMAGE="debian:12"
        ;;
    debian-13)
        CONTAINER_IMAGE="debian:trixie"
        ;;
    *)
        echo "Warning: Unknown distro '$DISTRO', using debian:12"
        CONTAINER_IMAGE="debian:12"
        ;;
esac

echo "=== Signing DEB in Docker container ==="
echo "DEB: $DEB_NAME"
echo "Distribution: $DISTRO"
echo "Container image: $CONTAINER_IMAGE"
echo ""

# Run signing in Docker container
docker run --rm \
    -v "$DEB_DIR:/debs:rw" \
    -e "GPG_KEY_BASE64=$GPG_KEY_BASE64" \
    -e "GPG_PASSPHRASE=$GPG_PASSPHRASE" \
    -e "GPG_KEY_ID=$GPG_KEY_ID" \
    "$CONTAINER_IMAGE" \
    bash -c "
        set -euo pipefail

        # Install required packages
        echo '==> Installing gnupg...'
        apt-get update -qq > /dev/null 2>&1
        apt-get install -y -qq gnupg dpkg > /dev/null 2>&1

        # Create temporary GPG home
        export GNUPGHOME=\$(mktemp -d)
        chmod 700 \"\$GNUPGHOME\"

        # Import GPG key
        echo '==> Importing GPG key...'
        echo \"\$GPG_KEY_BASE64\" | base64 -d | gpg --batch --import 2>&1 > /dev/null

        # Get fingerprint and trust the key
        FINGERPRINT=\$(gpg --list-keys --with-colons \"\$GPG_KEY_ID\" | awk -F: '/^fpr:/ {print \$10; exit}')
        echo \"\${FINGERPRINT}:6:\" | gpg --import-ownertrust 2>&1 > /dev/null

        # Sign the DEB
        echo '==> Signing DEB package...'
        if [ -n \"\$GPG_PASSPHRASE\" ]; then
            echo \"\$GPG_PASSPHRASE\" | gpg --batch --passphrase-fd 0 \
                --detach-sign --armor -u \"\$GPG_KEY_ID\" /debs/$DEB_NAME
        else
            gpg --batch --detach-sign --armor -u \"\$GPG_KEY_ID\" /debs/$DEB_NAME
        fi

        # Verify signature
        echo '==> Verifying signature...'
        gpg --verify /debs/${DEB_NAME}.asc /debs/$DEB_NAME 2>&1 | grep -E '(Good signature|Signature made)'

        # Cleanup
        rm -rf \"\$GNUPGHOME\"

        echo ''
        echo '✓ DEB signed successfully in container'
    "

echo ""
echo "✓ DEB signed and signature saved to: ${DEB_FILE}.asc"
