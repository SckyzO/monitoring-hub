#!/usr/bin/env python3
"""
Migrate all manifests to use single universal DEB target (debian-12).

This script updates all manifest.yaml files to use only debian-12 as the
DEB target, reflecting the new simplified build strategy where a single
universal DEB package is built on Debian 12 for maximum compatibility
across all Debian/Ubuntu distributions.
"""

import glob
import sys
from pathlib import Path

import yaml


def update_manifest(manifest_path):
    """Update a single manifest to use debian-12 only for DEB targets."""
    with open(manifest_path) as f:
        content = f.read()
        manifest = yaml.safe_load(content)

    if not manifest:
        return False

    # Check if DEB artifacts are defined
    deb_config = manifest.get("artifacts", {}).get("deb")
    if not deb_config or not deb_config.get("enabled"):
        return False

    # Get current targets
    current_targets = deb_config.get("targets", [])

    # If already using only debian-12, skip
    if current_targets == ["debian-12"]:
        print(f"  ℹ️  Already using debian-12 only: {manifest_path.name}")
        return False

    # Update targets to debian-12 only
    deb_config["targets"] = ["debian-12"]

    # Write back with preserved formatting
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, indent=2)

    print(f"  ✓ Updated {manifest_path.name}: {current_targets} → ['debian-12']")
    return True


def main():
    """Update all manifests in the exporters directory."""
    manifests = list(Path("exporters").glob("*/manifest.yaml"))

    print(f"Found {len(manifests)} manifests\n")

    updated = 0
    skipped = 0

    for manifest_path in sorted(manifests):
        if update_manifest(manifest_path):
            updated += 1
        else:
            skipped += 1

    print(f"\n✅ Migration complete:")
    print(f"   Updated: {updated}")
    print(f"   Skipped: {skipped} (no DEB or already debian-12)")
    print(f"\n💡 Universal DEB built on Debian 12, compatible with:")
    print(f"   - Ubuntu 20.04, 22.04, 24.04+")
    print(f"   - Debian 11, 12, 13+")


if __name__ == "__main__":
    main()
