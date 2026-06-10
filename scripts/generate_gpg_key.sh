#!/usr/bin/env bash
# Generate the GPG key used to sign RPM/DEB packages and repo metadata.
# Run this LOCALLY ONCE; the existing signing key is preserved in secrets/ and on
# GitHub Actions secrets. Regenerating breaks trust continuity for already-published
# packages, so only run this when bootstrapping a brand-new signing identity.
#
# Output lands in secrets/ (git-ignored). The private key is exported base64-encoded
# to survive single-line GitHub secret storage; forge-release.yml decodes it with
# `base64 -d` before `gpg --import`. The key is passphraseless on purpose: a CI key's
# passphrase would be stored as a secret right next to the key, adding no real
# protection.
set -euo pipefail

KEY_NAME="Monitoring Hub Package Signing"
KEY_EMAIL="noreply@monitoring-hub.local"
KEY_COMMENT="Automated package signing key"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SECRETS_DIR="$PROJECT_ROOT/secrets"

echo "=== Monitoring Hub GPG key generator ==="
echo "Secrets will be written to: $SECRETS_DIR"
echo ""

config="$(mktemp)"
trap 'rm -f "$config"' EXIT
cat >"$config" <<EOF
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
gpg --batch --generate-key "$config"

key_id="$(gpg --list-keys --with-colons "${KEY_EMAIL}" | awk -F: '/^pub:/ {print $5; exit}')"
if [ -z "$key_id" ]; then
  echo "Error: failed to generate key" >&2
  exit 1
fi
echo ""
echo "Key generated: ${key_id}"

mkdir -p "$SECRETS_DIR"
gpg --export-secret-keys --armor "${key_id}" | base64 -w 0 >"$SECRETS_DIR/GPG_PRIVATE_KEY"
gpg --export --armor "${key_id}" | base64 -w 0 >"$SECRETS_DIR/GPG_PUBLIC_KEY"
gpg --export --armor "${key_id}" >"$SECRETS_DIR/RPM-GPG-KEY-monitoring-hub"
printf '' >"$SECRETS_DIR/GPG_PASSPHRASE" # empty: key has no passphrase
echo "${key_id}" >"$SECRETS_DIR/GPG_KEY_ID"

cat >"$SECRETS_DIR/key_info.txt" <<EOF
=== GPG Key Information ===
Generated: $(date)
Key ID: ${key_id}
Key Name: ${KEY_NAME}
Key Email: ${KEY_EMAIL}

Files:
- GPG_PRIVATE_KEY: base64-encoded ASCII-armored private key (CI secret)
- GPG_PASSPHRASE: empty (key has no passphrase)
- GPG_KEY_ID: key identifier
- GPG_PUBLIC_KEY: base64-encoded ASCII-armored public key (CI secret)
- RPM-GPG-KEY-monitoring-hub: ASCII-armored public key for distribution

forge-release.yml consumes GPG_PRIVATE_KEY as: base64 -d | gpg --batch --import

NEVER commit this directory. Back it up to an encrypted vault.
EOF

chmod 700 "$SECRETS_DIR"
chmod 600 "$SECRETS_DIR"/*

echo ""
echo "Secrets written. Upload to GitHub with:"
echo "  gh secret set GPG_PRIVATE_KEY < $SECRETS_DIR/GPG_PRIVATE_KEY"
echo "  gh secret set GPG_PASSPHRASE < $SECRETS_DIR/GPG_PASSPHRASE"
echo "  gh secret set GPG_KEY_ID     < $SECRETS_DIR/GPG_KEY_ID"
echo "  gh secret set GPG_PUBLIC_KEY < $SECRETS_DIR/GPG_PUBLIC_KEY"
