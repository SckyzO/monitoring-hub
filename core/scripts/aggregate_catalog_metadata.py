#!/usr/bin/env python3
"""
Aggregate artifact metadata into exporter metadata.json.

Reads all granular artifact JSON files (rpm_*, deb_*, docker.json) and
aggregates them into a single metadata.json file per exporter.

This script is called by the portal generator to create the aggregated view.

Usage:
    python3 aggregate_catalog_metadata.py \\
        --exporter node_exporter \\
        --catalog-dir catalog \\
        --manifest-path exporters/node_exporter/manifest.yaml
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse manifest.yaml."""
    if not manifest_path.exists():
        print(f"Warning: Manifest not found: {manifest_path}")
        return {}

    with open(manifest_path) as f:
        return yaml.safe_load(f)


def load_artifacts(exporter_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all artifact JSON files for an exporter.
    Skips metadata.json to avoid circular dependency.
    """
    artifacts = []

    for json_file in exporter_dir.glob("*.json"):
        # Skip the aggregated metadata file
        if json_file.name == "metadata.json":
            continue

        try:
            with open(json_file) as f:
                artifact = json.load(f)
                artifacts.append(artifact)
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")

    return artifacts


def aggregate_rpm_artifacts(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate RPM artifacts by dist/arch."""
    rpm_data = {}

    for artifact in artifacts:
        if artifact.get("artifact_type") != "rpm":
            continue

        dist = artifact.get("dist")
        arch = artifact.get("arch")
        status = artifact.get("status", "unknown")

        if dist not in rpm_data:
            rpm_data[dist] = {}

        rpm_data[dist][arch] = {
            "status": status,
            "url": artifact.get("package", {}).get("url"),
            "size_bytes": artifact.get("package", {}).get("size_bytes"),
            "sha256": artifact.get("package", {}).get("sha256"),
            "build_date": artifact.get("build_date"),
        }

    return rpm_data


def aggregate_deb_artifacts(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate DEB artifacts by dist/arch."""
    deb_data = {}

    for artifact in artifacts:
        if artifact.get("artifact_type") != "deb":
            continue

        dist = artifact.get("dist")
        arch = artifact.get("arch")
        status = artifact.get("status", "unknown")

        if dist not in deb_data:
            deb_data[dist] = {}

        deb_data[dist][arch] = {
            "status": status,
            "url": artifact.get("package", {}).get("url"),
            "size_bytes": artifact.get("package", {}).get("size_bytes"),
            "sha256": artifact.get("package", {}).get("sha256"),
            "build_date": artifact.get("build_date"),
        }

    return deb_data


def aggregate_docker_artifacts(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate Docker artifacts."""
    for artifact in artifacts:
        if artifact.get("artifact_type") != "docker":
            continue

        return {
            "status": artifact.get("status", "unknown"),
            "images": artifact.get("images", []),
            "build_date": artifact.get("build_date"),
        }

    # No Docker artifact found
    return {"status": "na", "images": [], "build_date": None}


def compute_aggregate_status(artifacts_by_type: Dict[str, Any]) -> Dict[str, str]:
    """
    Compute aggregate status per artifact type.
    - success: At least one artifact succeeded
    - failed: All artifacts failed
    - pending: No successes, some pending
    - na: Not enabled
    """
    statuses = {}

    for artifact_type, data in artifacts_by_type.items():
        if artifact_type == "docker":
            statuses["docker"] = data.get("status", "na")
            continue

        # For RPM/DEB, check if at least one dist/arch succeeded
        has_success = False
        has_pending = False
        has_failed = False

        for dist_data in data.values():
            for arch_data in dist_data.values():
                status = arch_data.get("status", "unknown")
                if status == "success":
                    has_success = True
                elif status == "pending":
                    has_pending = True
                elif status == "failed":
                    has_failed = True

        if has_success:
            statuses[artifact_type] = "success"
        elif has_pending:
            statuses[artifact_type] = "pending"
        elif has_failed:
            statuses[artifact_type] = "failed"
        else:
            statuses[artifact_type] = "na"

    return statuses


def find_latest_build_date(artifacts: List[Dict[str, Any]]) -> str:
    """Find the most recent build_date from all artifacts."""
    dates = [a.get("build_date") for a in artifacts if a.get("build_date")]
    if not dates:
        return None
    return max(dates)


def aggregate_metadata(
    exporter: str, artifacts: List[Dict[str, Any]], manifest: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all artifacts into a single metadata.json structure.
    """
    # Aggregate by artifact type
    rpm_data = aggregate_rpm_artifacts(artifacts)
    deb_data = aggregate_deb_artifacts(artifacts)
    docker_data = aggregate_docker_artifacts(artifacts)

    # Compute aggregate statuses
    artifacts_by_type = {"rpm": rpm_data, "deb": deb_data, "docker": docker_data}
    statuses = compute_aggregate_status(artifacts_by_type)

    # Extract manifest info
    version = manifest.get("version", "unknown")
    category = manifest.get("category", "System")
    description = manifest.get("description", "")

    # Get latest build date
    last_updated = find_latest_build_date(artifacts)

    return {
        "format_version": "3.0",
        "exporter": exporter,
        "version": version.lstrip("v"),  # Normalize version
        "category": category,
        "description": description,
        "last_updated": last_updated,
        "artifacts": {
            "rpm": rpm_data,
            "deb": deb_data,
            "docker": docker_data,
        },
        "status": statuses,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate artifact metadata into exporter metadata.json"
    )
    parser.add_argument("--exporter", required=True, help="Exporter name")
    parser.add_argument(
        "--catalog-dir", required=True, help="Catalog root directory (e.g., catalog)"
    )
    parser.add_argument(
        "--manifest-path",
        required=True,
        help="Path to exporter manifest.yaml",
    )
    parser.add_argument(
        "--output", help="Output file (default: catalog/<exporter>/metadata.json)"
    )

    args = parser.parse_args()

    # Paths
    catalog_dir = Path(args.catalog_dir)
    exporter_dir = catalog_dir / args.exporter
    manifest_path = Path(args.manifest_path)

    # Load manifest
    manifest = load_manifest(manifest_path)

    # Load artifacts
    if not exporter_dir.exists():
        print(f"Error: Exporter directory not found: {exporter_dir}")
        sys.exit(1)

    artifacts = load_artifacts(exporter_dir)

    if not artifacts:
        print(f"Warning: No artifacts found for {args.exporter}")

    # Aggregate
    print(f"Aggregating {len(artifacts)} artifacts for {args.exporter}...")
    metadata = aggregate_metadata(args.exporter, artifacts, manifest)

    # Write output
    output_path = (
        Path(args.output) if args.output else exporter_dir / "metadata.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Aggregated metadata written to {output_path}")
    print(f"  Status: {metadata['status']}")


if __name__ == "__main__":
    main()
