#!/usr/bin/env python3
"""
Generate YUM repository metadata pointing to GitHub Releases.

This script creates repodata/ XML files that reference RPM packages
hosted on GitHub Releases instead of local files.
"""

import argparse
import glob
import gzip
import hashlib
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

import requests


def get_rpm_metadata(url: str, local_cache: Path) -> Dict:
    """
    Download RPM and extract metadata (name, version, arch, etc.).
    Cache locally to avoid repeated downloads.
    """
    # Create cache filename from URL
    cache_file = local_cache / hashlib.md5(url.encode()).hexdigest()

    if cache_file.exists():
        print(f"Using cached RPM: {cache_file.name}")
        rpm_path = cache_file
    else:
        print(f"Downloading RPM: {url}")
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        cache_file.write_bytes(response.content)
        rpm_path = cache_file

    # Extract RPM metadata using rpm command
    import subprocess

    result = subprocess.run(
        [
            "rpm",
            "-qp",
            "--queryformat",
            "%{NAME}|%{VERSION}|%{RELEASE}|%{ARCH}|%{SIZE}|%{SUMMARY}|%{LICENSE}",
            str(rpm_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    name, version, release, arch, size, summary, license_str = result.stdout.split("|")

    return {
        "name": name,
        "version": version,
        "release": release,
        "arch": arch,
        "size": int(size),
        "summary": summary,
        "license": license_str,
        "location": url,
        "checksum": hashlib.sha256(rpm_path.read_bytes()).hexdigest(),
    }


def create_primary_xml(packages: List[Dict], output_dir: Path):
    """Create primary.xml.gz with package metadata."""
    root = ET.Element("metadata", xmlns="http://linux.duke.edu/metadata/common")
    root.set("packages", str(len(packages)))

    for pkg in packages:
        package = ET.SubElement(root, "package", type="rpm")

        name = ET.SubElement(package, "name")
        name.text = pkg["name"]

        arch = ET.SubElement(package, "arch")
        arch.text = pkg["arch"]

        ET.SubElement(
            package,
            "version",
            epoch="0",
            ver=pkg["version"],
            rel=pkg["release"],
        )

        checksum = ET.SubElement(package, "checksum", type="sha256", pkgid="YES")
        checksum.text = pkg["checksum"]

        summary = ET.SubElement(package, "summary")
        summary.text = pkg["summary"]

        packager = ET.SubElement(package, "packager")
        packager.text = "Monitoring Hub"

        url_elem = ET.SubElement(package, "url")
        url_elem.text = "https://sckyzo.github.io/monitoring-hub"

        ET.SubElement(package, "time", file="0", build="0")

        ET.SubElement(
            package, "size", package=str(pkg["size"]), installed="0", archive="0"
        )

        ET.SubElement(package, "location", href=pkg["location"])

        format_elem = ET.SubElement(package, "format")
        license_elem = ET.SubElement(format_elem, "rpm:license")
        license_elem.text = pkg["license"]

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    primary_xml = output_dir / "primary.xml"
    tree.write(primary_xml, encoding="utf-8", xml_declaration=True)

    # Compress
    with open(primary_xml, "rb") as f_in:
        with gzip.open(f"{primary_xml}.gz", "wb") as f_out:
            f_out.writelines(f_in)

    os.remove(primary_xml)
    print(f"Created {primary_xml}.gz")


def create_repomd_xml(repodata_dir: Path):
    """Create repomd.xml index."""
    root = ET.Element("repomd", xmlns="http://linux.duke.edu/metadata/repo")

    primary_gz = repodata_dir / "primary.xml.gz"

    data = ET.SubElement(root, "data", type="primary")
    ET.SubElement(data, "location", href=f"repodata/{primary_gz.name}")

    checksum = ET.SubElement(data, "checksum", type="sha256")
    checksum.text = hashlib.sha256(primary_gz.read_bytes()).hexdigest()

    size = ET.SubElement(data, "size")
    size.text = str(primary_gz.stat().st_size)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")

    repomd_xml = repodata_dir / "repomd.xml"
    tree.write(repomd_xml, encoding="utf-8", xml_declaration=True)
    print(f"Created {repomd_xml}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate YUM metadata for GitHub Releases"
    )
    parser.add_argument(
        "--release-urls-dir",
        required=True,
        help="Directory containing release_urls.json files",
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory for repodata/"
    )
    parser.add_argument("--dist", required=True, help="Distribution (el8, el9, el10)")
    parser.add_argument("--arch", required=True, help="Architecture (x86_64, aarch64)")
    parser.add_argument(
        "--cache-dir",
        default="/tmp/rpm-metadata-cache",
        help="Cache directory for downloaded RPMs",
    )

    args = parser.parse_args()

    release_urls_dir = Path(args.release_urls_dir)
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)

    # Create directories
    repodata_dir = output_dir / args.dist / args.arch / "repodata"
    repodata_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Find all release_urls.json files
    json_files = glob.glob(
        str(release_urls_dir / "**" / "release_urls.json"), recursive=True
    )

    if not json_files:
        print("No release_urls.json files found")
        sys.exit(1)

    print(f"Found {len(json_files)} release URL files")

    # Collect all RPM URLs matching dist/arch
    packages = []
    for json_file in json_files:
        with open(json_file, "r") as f:
            data = json.load(f)

        for asset in data.get("assets", []):
            filename = asset["file"]

            # Filter by dist and arch
            if f".{args.dist}." in filename and args.arch in filename:
                print(f"Processing: {filename}")

                try:
                    metadata = get_rpm_metadata(asset["url"], cache_dir)
                    packages.append(metadata)
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
                    continue

    if not packages:
        print(f"No RPM packages found for {args.dist}/{args.arch}")
        sys.exit(1)

    print(f"\nGenerating metadata for {len(packages)} packages...")

    # Create primary.xml.gz
    create_primary_xml(packages, repodata_dir)

    # Create repomd.xml
    create_repomd_xml(repodata_dir)

    print(f"\nYUM metadata generated successfully in {repodata_dir}")


if __name__ == "__main__":
    main()
