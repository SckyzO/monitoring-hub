#!/usr/bin/env python3
"""
Validate an exporter manifest against the schema.

Usage:
    python3 core/scripts/validate_manifest.py exporters/node_exporter/manifest.yaml
"""

import sys
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.engine.schema import ManifestSchema


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 validate_manifest.py <manifest.yaml>")
        sys.exit(1)

    manifest_path = sys.argv[1]
    exporter_name = Path(manifest_path).parent.name

    try:
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load {manifest_path}: {e}")
        sys.exit(1)

    schema = ManifestSchema()
    errors = schema.validate(data)

    if errors:
        print(f"❌ Validation failed for {exporter_name}:")
        for field, msgs in errors.items():
            msgs_list = msgs if isinstance(msgs, list) else [msgs]
            for msg in msgs_list:
                print(f"  - {field}: {msg}")
        sys.exit(1)
    else:
        print(f"✓ Valid: {exporter_name}")


if __name__ == "__main__":
    main()
