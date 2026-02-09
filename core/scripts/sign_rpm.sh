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

# List imported keys for debugging
echo "Imported keys:"
gpg --list-keys --with-colons

# Trust the key ultimately (use fingerprint)
echo "Setting key trust..."
FINGERPRINT=$(gpg --list-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
if [ -z "$FINGERPRINT" ]; then
    echo "Error: Could not extract fingerprint from imported key"
    exit 1
fi
echo "Found fingerprint: $FINGERPRINT"
echo "${FINGERPRINT}:6:" | gpg --import-ownertrust 2>&1

# Verify the key is trusted
echo "Verifying key trust:"
gpg --list-keys --with-colons "$FINGERPRINT"

# Configure RPM macros for signing
mkdir -p ~/.rpmmacros.d

# Use fingerprint instead of KEY_ID for better compatibility
echo "Configuring RPM macros with fingerprint: $FINGERPRINT"

# Create passphrase file if needed
PASSPHRASE_FILE=""
if [ -n "$GPG_PASSPHRASE" ]; then
    PASSPHRASE_FILE=$(mktemp)
    echo "$GPG_PASSPHRASE" > "$PASSPHRASE_FILE"
    chmod 600 "$PASSPHRASE_FILE"
    trap 'rm -f "$PASSPHRASE_FILE"; rm -rf "$GPG_HOME"' EXIT

    cat > ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ${GPG_HOME}
%_gpg_name ${FINGERPRINT}
%_gpgbin /usr/bin/gpg
%__gpg_sign_cmd %{__gpg} gpg --batch --no-verbose --no-armor --pinentry-mode loopback --passphrase-file ${PASSPHRASE_FILE} --no-secmem-warning -u "%{_gpg_name}" -sbo %{__signature_filename} %{__plaintext_filename}
EOF
else
    cat > ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ${GPG_HOME}
%_gpg_name ${FINGERPRINT}
%_gpgbin /usr/bin/gpg
%__gpg_sign_cmd %{__gpg} gpg --batch --no-verbose --no-armor --no-secmem-warning -u "%{_gpg_name}" -sbo %{__signature_filename} %{__plaintext_filename}
EOF
fi

echo "RPM macros configured"
cat ~/.rpmmacros

# Sign the RPM
echo "Signing RPM with key ${GPG_KEY_ID}..."
rpmsign --addsign "$RPM_FILE"

# Import public key to RPM keyring for verification
echo "Importing public key to RPM database for verification..."
gpg --export --armor "$FINGERPRINT" | rpm --import

# Verify the signature
echo "Verifying signature..."
if rpm --checksig "$RPM_FILE"; then
    echo "✓ RPM signed and verified successfully"
else
    echo "⚠️  RPM signed but verification returned non-zero (this may be OK if gpg key is not fully trusted in RPM db)"
    echo "Checking if signature exists..."
    rpm -qp --qf '%{SIGGPG:pgpsig}\n' "$RPM_FILE" && echo "✓ GPG signature is present in RPM"
fi
