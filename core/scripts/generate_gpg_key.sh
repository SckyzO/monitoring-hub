#!/bin/bash
# Generate GPG key for signing RPM and DEB packages
# This script should be run LOCALLY ONCE to generate the GPG key
# The output will be saved to secrets/ directory

set -euo pipefail

KEY_NAME="Monitoring Hub Package Signing"
KEY_EMAIL="noreply@monitoring-hub.local"
KEY_COMMENT="Automated package signing key"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SECRETS_DIR="$PROJECT_ROOT/secrets"

echo "=== Monitoring Hub GPG Key Generator ==="
echo ""
echo "This will generate a GPG key for signing packages."
echo "Secrets will be saved to: $SECRETS_DIR"
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

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

# Save all secrets to files
echo "${PRIVATE_KEY}" > "$SECRETS_DIR/GPG_PRIVATE_KEY"
echo "" > "$SECRETS_DIR/GPG_PASSPHRASE"  # Empty passphrase
echo "${KEY_ID}" > "$SECRETS_DIR/GPG_KEY_ID"
echo "${PUBLIC_KEY}" > "$SECRETS_DIR/GPG_PUBLIC_KEY"
echo "${PUBLIC_KEY_ASCII}" > "$SECRETS_DIR/RPM-GPG-KEY-monitoring-hub"

# Save metadata
cat > "$SECRETS_DIR/key_info.txt" <<EOF
=== GPG Key Information ===
Generated: $(date)
Key ID: ${KEY_ID}
Key Name: ${KEY_NAME}
Key Email: ${KEY_EMAIL}

This directory contains:
- GPG_PRIVATE_KEY: Base64-encoded private key for signing
- GPG_PASSPHRASE: Empty (key has no passphrase)
- GPG_KEY_ID: Key identifier
- GPG_PUBLIC_KEY: Base64-encoded public key for GitHub secret
- RPM-GPG-KEY-monitoring-hub: ASCII-armored public key for distribution

⚠️  SECURITY WARNING ⚠️
Keep these files secure! Never commit to git.
Backup to a secure location (password manager, encrypted vault).
EOF

chmod 600 "$SECRETS_DIR"/*
chmod 700 "$SECRETS_DIR"

echo ""
echo "=== Secrets Saved Successfully ==="
echo "Location: $SECRETS_DIR"
echo ""
ls -lh "$SECRETS_DIR"
echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Review the secrets:"
echo "   cat $SECRETS_DIR/key_info.txt"
echo ""
echo "2. Upload secrets to GitHub using gh CLI:"
echo "   gh secret set GPG_PRIVATE_KEY < $SECRETS_DIR/GPG_PRIVATE_KEY"
echo "   gh secret set GPG_PASSPHRASE < $SECRETS_DIR/GPG_PASSPHRASE"
echo "   gh secret set GPG_KEY_ID < $SECRETS_DIR/GPG_KEY_ID"
echo "   gh secret set GPG_PUBLIC_KEY < $SECRETS_DIR/GPG_PUBLIC_KEY"
echo ""
echo "3. Or run the helper script that will be generated:"
echo "   ./secrets/upload_to_github.sh"
echo ""

# Create upload helper script
cat > "$SECRETS_DIR/upload_to_github.sh" <<'UPLOADEOF'
#!/bin/bash
# Upload GPG secrets to GitHub using gh CLI
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Uploading GPG secrets to GitHub ==="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: gh CLI is not installed"
    echo "Install from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub"
    echo "Run: gh auth login"
    exit 1
fi

# Upload secrets
echo "Uploading GPG_PRIVATE_KEY..."
gh secret set GPG_PRIVATE_KEY < "$SCRIPT_DIR/GPG_PRIVATE_KEY"

echo "Uploading GPG_PASSPHRASE..."
gh secret set GPG_PASSPHRASE < "$SCRIPT_DIR/GPG_PASSPHRASE"

echo "Uploading GPG_KEY_ID..."
gh secret set GPG_KEY_ID < "$SCRIPT_DIR/GPG_KEY_ID"

echo "Uploading GPG_PUBLIC_KEY..."
gh secret set GPG_PUBLIC_KEY < "$SCRIPT_DIR/GPG_PUBLIC_KEY"

echo ""
echo "✓ All secrets uploaded successfully!"
echo ""
echo "Verify with: gh secret list"
UPLOADEOF

chmod +x "$SECRETS_DIR/upload_to_github.sh"

echo "Helper script created: $SECRETS_DIR/upload_to_github.sh"
echo ""
echo "⚠️  IMPORTANT: Backup these secrets to a secure location!"
