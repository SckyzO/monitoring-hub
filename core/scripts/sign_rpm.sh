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
echo "$GPG_KEY_BASE64" | base64 -d | gpg --batch --import

# Trust the key ultimately
echo "${GPG_KEY_ID}:6:" | gpg --import-ownertrust

# Configure RPM macros for signing
mkdir -p ~/.rpmmacros.d
cat > ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_path ${GPG_HOME}
%_gpg_name ${GPG_KEY_ID}
%_gpgbin /usr/bin/gpg
%__gpg_sign_cmd %{__gpg} \\
    gpg --batch --no-verbose --no-armor \\
    %{?_gpg_digest_algo:--digest-algo %{_gpg_digest_algo}} \\
    --no-secmem-warning \\
    -u "%{_gpg_name}" -sbo %{__signature_filename} %{__plaintext_filename}
EOF

# Sign the RPM
echo "Signing RPM with key ${GPG_KEY_ID}..."
if [ -n "$GPG_PASSPHRASE" ]; then
    echo "$GPG_PASSPHRASE" | rpmsign --addsign "$RPM_FILE"
else
    rpmsign --addsign "$RPM_FILE"
fi

# Verify the signature
echo "Verifying signature..."
rpm --checksig "$RPM_FILE"

echo "✓ RPM signed successfully"
