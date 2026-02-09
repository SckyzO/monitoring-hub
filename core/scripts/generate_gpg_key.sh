#!/bin/bash
# Generate GPG key for signing RPM and DEB packages
# This script should be run LOCALLY ONCE to generate the GPG key
# The output should be added to GitHub Secrets

set -euo pipefail

KEY_NAME="Monitoring Hub Package Signing"
KEY_EMAIL="noreply@monitoring-hub.local"
KEY_COMMENT="Automated package signing key"

echo "=== Monitoring Hub GPG Key Generator ==="
echo ""
echo "This will generate a GPG key for signing packages."
echo "Please enter a strong passphrase when prompted."
echo ""

# Generate key with batch mode
cat > gpg_key_config.txt <<EOF
%echo Generating GPG key...
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: ${KEY_NAME}
Name-Comment: ${KEY_COMMENT}
Name-Email: ${KEY_EMAIL}
Expire-Date: 0
%no-protection
%commit
%echo Done
EOF

echo "Generating RSA-4096 key... (this may take a few minutes)"
gpg --batch --generate-key gpg_key_config.txt

# Get the key ID
KEY_ID=$(gpg --list-keys --with-colons "${KEY_EMAIL}" | awk -F: '/^pub:/ {print $5}')

if [ -z "$KEY_ID" ]; then
    echo "Error: Failed to generate key"
    rm -f gpg_key_config.txt
    exit 1
fi

echo ""
echo "=== Key generated successfully ==="
echo "Key ID: ${KEY_ID}"
echo ""

# Export private key (base64 encoded)
PRIVATE_KEY=$(gpg --export-secret-keys --armor "${KEY_ID}" | base64 -w 0)

# Export public key (base64 encoded for secret, ASCII-armored for publication)
PUBLIC_KEY=$(gpg --export --armor "${KEY_ID}" | base64 -w 0)
PUBLIC_KEY_ASCII=$(gpg --export --armor "${KEY_ID}")

# Clean up
rm -f gpg_key_config.txt

echo "=== GitHub Secrets Configuration ==="
echo ""
echo "Add these four secrets to your GitHub repository:"
echo "(Settings > Secrets and variables > Actions > New repository secret)"
echo ""
echo "1. GPG_PRIVATE_KEY"
echo "-------------------"
echo "${PRIVATE_KEY}"
echo ""
echo "2. GPG_PASSPHRASE"
echo "-----------------"
echo "(Leave empty - key was generated without passphrase)"
echo ""
echo "3. GPG_KEY_ID"
echo "-------------"
echo "${KEY_ID}"
echo ""
echo "4. GPG_PUBLIC_KEY"
echo "-----------------"
echo "${PUBLIC_KEY}"
echo ""
echo "=== Public Key for Documentation ==="
echo ""
echo "This is the public key users will import:"
echo ""
echo "${PUBLIC_KEY_ASCII}"
echo ""
echo "Save this to a file named 'RPM-GPG-KEY-monitoring-hub' for distribution"
