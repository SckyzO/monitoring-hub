#!/usr/bin/env python3
"""
Generate artifact metadata JSON files for catalog.

This script creates atomic, per-artifact JSON files that are written by individual
build jobs. No race conditions, no concurrent writes to same file.

Usage:
    python3 generate_artifact_metadata.py \\
        --type rpm \\
        --exporter node_exporter \\
        --version 1.10.2 \\
        --arch amd64 \\
        --dist el9 \\
        --filename node_exporter-1.10.2-1.el9.x86_64.rpm \\
        --url https://github.com/.../node_exporter-1.10.2-1.el9.x86_64.rpm \\
        --sha256 abc123... \\
        --size 12345678 \\
        --output catalog/node_exporter/rpm_amd64_el9.json
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import requests


def get_rpm_metadata(url: str, cache_dir: Path) -> Dict[str, Any]:
    """
    Download RPM and extract metadata using rpm command.
    Returns dict with RPM-specific fields.
    """
    cache_file = cache_dir / hashlib.md5(
        url.encode(), usedforsecurity=False
    ).hexdigest()

    if cache_file.exists():
        print(f"Using cached RPM: {cache_file.name}")
        rpm_path = cache_file
    else:
        print(f"Downloading RPM: {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        cache_file.write_bytes(response.content)
        rpm_path = cache_file

    # Extract RPM metadata
    result = subprocess.run(
        [
            "rpm",
            "-qp",
            "--queryformat",
            "%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|%{SUMMARY}|%{LICENSE}",
            str(rpm_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    name, version, release, arch, summary, license_str = result.stdout.split("|")

    return {
        "name": name,
        "version": version,
        "release": release,
        "arch": arch,
        "summary": summary,
        "license": license_str,
    }


def get_deb_metadata(url: str, cache_dir: Path) -> Dict[str, Any]:
    """
    Download DEB and extract metadata using dpkg-deb command.
    Returns dict with DEB-specific fields.
    """
    cache_file = cache_dir / hashlib.md5(
        url.encode(), usedforsecurity=False
    ).hexdigest()

    if cache_file.exists():
        print(f"Using cached DEB: {cache_file.name}")
        deb_path = cache_file
    else:
        print(f"Downloading DEB: {url}")
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        cache_file.write_bytes(response.content)
        deb_path = cache_file

    # Extract DEB control file
    result = subprocess.run(
        ["dpkg-deb", "--field", str(deb_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    # Parse control file
    control = {}
    for line in result.stdout.strip().split("\n"):
        if ": " in line:
            key, value = line.split(": ", 1)
            control[key] = value

    return {
        "package": control.get("Package", "unknown"),
        "version": control.get("Version", "0.0.0"),
        "architecture": control.get("Architecture", "amd64"),
        "maintainer": control.get("Maintainer", "Monitoring Hub"),
        "description": control.get("Description", ""),
        "section": control.get("Section", "net"),
        "priority": control.get("Priority", "optional"),
    }


def generate_rpm_metadata(args: argparse.Namespace, cache_dir: Path) -> Dict[str, Any]:
    """Generate metadata JSON for RPM artifact."""
    # Extract RPM-specific metadata if URL provided
    rpm_metadata = {}
    if args.url and args.extract_metadata:
        try:
            rpm_metadata = get_rpm_metadata(args.url, cache_dir)
        except Exception as e:
            print(f"Warning: Could not extract RPM metadata: {e}")

    return {
        "format_version": "3.0",
        "artifact_type": "rpm",
        "exporter": args.exporter,
        "version": args.version,
        "arch": args.arch,
        "dist": args.dist,
        "build_date": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "package": {
            "filename": args.filename,
            "url": args.url,
            "sha256": args.sha256,
            "size_bytes": args.size,
        },
        "rpm_metadata": rpm_metadata,
    }


def generate_deb_metadata(args: argparse.Namespace, cache_dir: Path) -> Dict[str, Any]:
    """Generate metadata JSON for DEB artifact."""
    # Extract DEB-specific metadata if URL provided
    deb_metadata = {}
    if args.url and args.extract_metadata:
        try:
            deb_metadata = get_deb_metadata(args.url, cache_dir)
        except Exception as e:
            print(f"Warning: Could not extract DEB metadata: {e}")

    return {
        "format_version": "3.0",
        "artifact_type": "deb",
        "exporter": args.exporter,
        "version": args.version,
        "arch": args.arch,
        "dist": args.dist,
        "build_date": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "package": {
            "filename": args.filename,
            "url": args.url,
            "sha256": args.sha256,
            "size_bytes": args.size,
        },
        "deb_metadata": deb_metadata,
    }


def generate_docker_metadata(args: argparse.Namespace) -> Dict[str, Any]:
    """Generate metadata JSON for Docker artifact."""
    images = []
    if args.docker_images:
        # Parse docker images JSON
        images = json.loads(args.docker_images)

    return {
        "format_version": "3.0",
        "artifact_type": "docker",
        "exporter": args.exporter,
        "version": args.version,
        "build_date": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "images": images,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate artifact metadata JSON for catalog"
    )

    # Required arguments
    parser.add_argument(
        "--type",
        required=True,
        choices=["rpm", "deb", "docker"],
        help="Artifact type",
    )
    parser.add_argument("--exporter", required=True, help="Exporter name")
    parser.add_argument("--version", required=True, help="Exporter version")
    parser.add_argument(
        "--output", required=True, help="Output JSON file path (will be created)"
    )

    # Status
    parser.add_argument(
        "--status",
        default="success",
        choices=["success", "failed", "pending"],
        help="Build status (default: success)",
    )

    # RPM/DEB specific
    parser.add_argument("--arch", help="Architecture (amd64, arm64, etc)")
    parser.add_argument(
        "--dist", help="Distribution (el8, el9, ubuntu-22.04, etc)"
    )
    parser.add_argument("--filename", help="Package filename")
    parser.add_argument("--url", help="Package download URL")
    parser.add_argument("--sha256", help="SHA256 checksum")
    parser.add_argument("--size", type=int, help="File size in bytes")

    # Docker specific
    parser.add_argument(
        "--docker-images",
        help='JSON array of Docker images (e.g., \'[{"registry":"ghcr.io","tag":"1.0.0"}]\')',
    )

    # Optional
    parser.add_argument(
        "--extract-metadata",
        action="store_true",
        help="Extract detailed metadata from package (requires downloading)",
    )
    parser.add_argument(
        "--cache-dir",
        default=f"{tempfile.gettempdir()}/artifact-metadata-cache",
        help="Cache directory for downloads",
    )

    args = parser.parse_args()

    # Validate required fields per type
    if args.type in ["rpm", "deb"]:
        required = ["arch", "dist", "filename", "url", "sha256", "size"]
        missing = [f for f in required if getattr(args, f) is None]
        if missing:
            print(f"Error: Missing required fields for {args.type}: {missing}")
            sys.exit(1)
    elif args.type == "docker":
        if not args.docker_images:
            print("Error: --docker-images required for docker type")
            sys.exit(1)

    # Create cache dir
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Generate metadata based on type
    print(f"Generating {args.type} metadata for {args.exporter} v{args.version}...")

    if args.type == "rpm":
        metadata = generate_rpm_metadata(args, cache_dir)
    elif args.type == "deb":
        metadata = generate_deb_metadata(args, cache_dir)
    elif args.type == "docker":
        metadata = generate_docker_metadata(args)
    else:
        print(f"Error: Unknown artifact type: {args.type}")
        sys.exit(1)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✓ Metadata written to {output_path}")


if __name__ == "__main__":
    main()
