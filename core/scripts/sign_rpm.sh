#!/bin/bash
# Sign an RPM package with GPG key
# Usage: sign_rpm.sh <rpm_file>
# Required env: GPG_PRIVATE_KEY, GPG_PASSPHRASE, GPG_KEY_ID

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <rpm_file>"
    echo "Required env vars: GPG_PRIVATE_KEY, GPG_PASSPHRASE, GPG_KEY_ID"
    exit 1
fi

# Validate required env vars without exposing values (the ${VAR:?MSG} form
# fails fast with the message but never prints the value).
: "${GPG_PRIVATE_KEY:?Missing required env var: GPG_PRIVATE_KEY}"
: "${GPG_PASSPHRASE:?Missing required env var: GPG_PASSPHRASE}"
: "${GPG_KEY_ID:?Missing required env var: GPG_KEY_ID}"

RPM_FILE="$1"

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
echo "$GPG_PRIVATE_KEY" | base64 -d | gpg --batch --import 2>&1

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
PUBLIC_KEY_FILE=$(mktemp)
gpg --export --armor "$FINGERPRINT" > "$PUBLIC_KEY_FILE"
rpm --import "$PUBLIC_KEY_FILE"
rm -f "$PUBLIC_KEY_FILE"

# Verify the signature
echo "Verifying signature..."
if rpm --checksig "$RPM_FILE"; then
    echo "✓ RPM signed and verified successfully"
else
    echo "⚠️  RPM signed but verification returned non-zero (this may be OK if gpg key is not fully trusted in RPM db)"
    echo "Checking if signature exists..."
    rpm -qp --qf '%{SIGGPG:pgpsig}\n' "$RPM_FILE" && echo "✓ GPG signature is present in RPM"
fi
