#!/bin/bash
# Sign an RPM package with GPG key
# Usage: sign_rpm.sh <rpm_file> <gpg_key_base64> <passphrase> <key_id>

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

echo "=== Signing RPM: $(basename "$RPM_FILE") ==="

# Create temporary GPG home directory
GPG_HOME=$(mktemp -d)
export GNUPGHOME="$GPG_HOME"
chmod 700 "$GPG_HOME"

# Cleanup on exit
trap 'rm -rf "$GPG_HOME"' EXIT

# Import GPG key
echo "Importing GPG key..."
echo "$GPG_KEY_BASE64" | base64 -d | gpg --batch --import 2>&1

# Trust the key ultimately (use fingerprint, not key ID)
FINGERPRINT=$(gpg --list-keys --with-colons "${GPG_KEY_ID}" | awk -F: '/^fpr:/ {print $10; exit}')
echo "${FINGERPRINT}:6:" | gpg --import-ownertrust 2>&1

# Create passphrase file if needed
PASSPHRASE_OPTS=""
if [ -n "$GPG_PASSPHRASE" ]; then
    PASSPHRASE_FILE=$(mktemp)
    echo "$GPG_PASSPHRASE" > "$PASSPHRASE_FILE"
    chmod 600 "$PASSPHRASE_FILE"
    trap 'rm -f "$PASSPHRASE_FILE"; rm -rf "$GPG_HOME"' EXIT
    PASSPHRASE_OPTS="--pinentry-mode loopback --passphrase-file $PASSPHRASE_FILE"
fi

# Configure RPM macros for signing
mkdir -p ~/.rpmmacros.d
cat > ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ${GPG_HOME}
%_gpg_name ${GPG_KEY_ID}
%_gpgbin /usr/bin/gpg
%__gpg_sign_cmd %{__gpg} \\
    gpg --batch --no-verbose --no-armor ${PASSPHRASE_OPTS} \\
    %{?_gpg_digest_algo:--digest-algo %{_gpg_digest_algo}} \\
    --no-secmem-warning \\
    -u "%{_gpg_name}" -sbo %{__signature_filename} %{__plaintext_filename}
EOF

# Sign the RPM
echo "Signing RPM with key ${GPG_KEY_ID}..."
rpmsign --addsign "$RPM_FILE"

# Verify the signature
echo "Verifying signature..."
rpm --checksig "$RPM_FILE"

echo "✓ RPM signed successfully"
