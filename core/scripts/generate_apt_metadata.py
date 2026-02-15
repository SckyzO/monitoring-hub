#!/usr/bin/env python3
"""
Generate APT repository metadata pointing to GitHub Releases.

This script creates Packages, Packages.gz, Release, and InRelease files
that reference DEB packages hosted on GitHub Releases.
"""

import argparse
import glob
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

import requests

# Mapping from our dist names to Debian/Ubuntu codenames
CODENAME_MAP = {
    "ubuntu-22.04": "jammy",
    "ubuntu-24.04": "noble",
    "debian-12": "bookworm",
    "debian-13": "trixie",
}


def get_deb_metadata(url: str, local_cache: Path) -> Dict:
    """
    Download DEB and extract metadata.
    Cache locally to avoid repeated downloads.
    """
    # MD5 used only for cache filename generation, not for security
    cache_file = (
        local_cache / hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()
    )  # nosec B324

    if cache_file.exists():
        print(f"Using cached DEB: {cache_file.name}")
        deb_path = cache_file
    else:
        print(f"Downloading DEB: {url}")
        response = requests.get(url, timeout=60)
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

    # Get file size and checksums
    deb_content = deb_path.read_bytes()

    return {
        "Package": control.get("Package", "unknown"),
        "Version": control.get("Version", "0.0.0"),
        "Architecture": control.get("Architecture", "amd64"),
        "Maintainer": control.get(
            "Maintainer", "Monitoring Hub <bot@monitoring-hub.local>"
        ),
        "Description": control.get("Description", ""),
        "Section": control.get("Section", "net"),
        "Priority": control.get("Priority", "optional"),
        "Size": str(len(deb_content)),
        "Filename": url,
        "SHA256": hashlib.sha256(deb_content).hexdigest(),
        # MD5sum required by Debian package format specification
        "MD5sum": hashlib.md5(deb_content, usedforsecurity=False).hexdigest(),  # nosec B324
    }


def create_packages_file(packages: List[Dict], output_dir: Path):
    """Create Packages and Packages.gz files."""
    packages_file = output_dir / "Packages"

    with open(packages_file, "w") as f:
        for pkg in packages:
            f.write(f"Package: {pkg['Package']}\n")
            f.write(f"Version: {pkg['Version']}\n")
            f.write(f"Architecture: {pkg['Architecture']}\n")
            f.write(f"Maintainer: {pkg['Maintainer']}\n")
            f.write(f"Filename: {pkg['Filename']}\n")
            f.write(f"Size: {pkg['Size']}\n")
            f.write(f"MD5sum: {pkg['MD5sum']}\n")
            f.write(f"SHA256: {pkg['SHA256']}\n")
            f.write(f"Section: {pkg['Section']}\n")
            f.write(f"Priority: {pkg['Priority']}\n")
            f.write(f"Description: {pkg['Description']}\n")
            f.write("\n")

    # Compress
    with open(packages_file, "rb") as f_in:
        with gzip.open(f"{packages_file}.gz", "wb") as f_out:
            f_out.writelines(f_in)

    print(f"Created {packages_file} and {packages_file}.gz")


def create_release_file(codename: str, arch: str, packages_dir: Path):
    """Create Release file for the distribution."""
    packages_file = packages_dir / "Packages"
    packages_gz = packages_dir / "Packages.gz"

    release_content = f"""Origin: Monitoring Hub
Label: Monitoring Hub
Suite: {codename}
Codename: {codename}
Architectures: {arch}
Components: main
Description: Monitoring Hub APT Repository
"""

    # Calculate checksums for Packages files
    # MD5Sum required by APT repository format specification
    release_content += "MD5Sum:\n"
    for file in [packages_file, packages_gz]:
        if file.exists():
            content = file.read_bytes()
            md5 = hashlib.md5(content, usedforsecurity=False).hexdigest()  # nosec B324
            size = len(content)
            rel_path = file.relative_to(packages_dir.parent.parent)
            release_content += f" {md5} {size} {rel_path}\n"

    release_content += "SHA256:\n"
    for file in [packages_file, packages_gz]:
        if file.exists():
            content = file.read_bytes()
            sha256 = hashlib.sha256(content).hexdigest()
            size = len(content)
            rel_path = file.relative_to(packages_dir.parent.parent)
            release_content += f" {sha256} {size} {rel_path}\n"

    release_file = packages_dir.parent.parent / "Release"
    release_file.write_text(release_content)
    print(f"Created {release_file}")

    return release_file


def scan_existing_packages_from_github(
    repo: str, dist: str, arch: str, cache_dir: Path
) -> List[Dict]:
    """
    Scan all existing DEB packages from GitHub Releases.
    Returns metadata for all packages across all releases.
    """
    packages = []

    print(f"\n🔍 Scanning existing packages from GitHub Releases for {dist}/{arch}...")

    try:
        # Get all releases from GitHub API
        import subprocess
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/releases", "--paginate", "--jq", ".[]"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )

        releases_data = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    releases_data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        print(f"Found {len(releases_data)} releases on GitHub")

        # Process each release
        for release in releases_data:
            assets = release.get("assets", [])

            for asset in assets:
                filename = asset.get("name", "")
                url = asset.get("browser_download_url", "")

                # Filter by arch (DEB naming: package_version_arch.deb)
                if filename.endswith(".deb") and f"_{arch}.deb" in filename:
                    print(f"  Found: {filename}")
                    try:
                        metadata = get_deb_metadata(url, cache_dir)
                        packages.append(metadata)
                    except Exception as e:
                        print(f"  ⚠️  Error processing {filename}: {e}")
                        continue

        print(f"✓ Loaded {len(packages)} existing packages from GitHub")

    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to fetch releases from GitHub: {e}")
        print("Continuing with only new packages...")
    except Exception as e:
        print(f"⚠️  Unexpected error scanning GitHub releases: {e}")
        print("Continuing with only new packages...")

    return packages


def deduplicate_packages(packages: List[Dict]) -> List[Dict]:
    """
    Remove duplicate packages, keeping the newest version.
    Packages are identified by (Package, Architecture) tuple.
    """
    from packaging import version

    # Group by (Package, Architecture)
    package_map = {}

    for pkg in packages:
        key = (pkg["Package"], pkg["Architecture"])

        if key not in package_map:
            package_map[key] = pkg
        else:
            # Compare versions
            try:
                existing_ver = version.parse(package_map[key]["Version"])
                new_ver = version.parse(pkg["Version"])

                if new_ver > existing_ver:
                    package_map[key] = pkg
                    print(f"  Replacing {key[0]} {existing_ver} with {new_ver}")
            except Exception as e:
                print(f"  ⚠️  Version comparison failed for {key[0]}: {e}")
                # Keep existing on error

    return list(package_map.values())


def main():
    parser = argparse.ArgumentParser(
        description="Generate APT metadata for GitHub Releases (cumulative mode)"
    )
    parser.add_argument(
        "--release-urls-dir",
        required=False,
        help="Directory containing release_urls.json files from current build",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory for apt/")
    parser.add_argument(
        "--dist",
        required=True,
        help="Distribution (ubuntu-22.04, ubuntu-24.04, debian-12, debian-13)",
    )
    parser.add_argument("--arch", required=True, help="Architecture (amd64, arm64)")
    parser.add_argument(
        "--repo",
        default="SckyzO/monitoring-hub",
        help="GitHub repository (owner/name)",
    )
    parser.add_argument(
        "--cache-dir",
        default=f"{tempfile.gettempdir()}/deb-metadata-cache",
        help="Cache directory for downloaded DEBs",
    )

    args = parser.parse_args()

    if args.dist not in CODENAME_MAP:
        print(f"Unknown distribution: {args.dist}")
        sys.exit(1)

    codename = CODENAME_MAP[args.dist]

    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)

    # Create directory structure: apt/dists/{codename}/main/binary-{arch}/
    packages_dir = output_dir / "dists" / codename / "main" / f"binary-{args.arch}"
    packages_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("APT Metadata Generator (Cumulative Mode)")
    print(f"Distribution: {args.dist} ({codename}) | Architecture: {args.arch}")
    print("=" * 80)

    # STEP 1: Scan ALL existing packages from GitHub Releases (cumulative)
    all_packages = scan_existing_packages_from_github(
        args.repo, args.dist, args.arch, cache_dir
    )

    # STEP 2: Add new packages from current build (if release_urls_dir provided)
    new_packages_count = 0
    if args.release_urls_dir:
        release_urls_dir = Path(args.release_urls_dir)

        if release_urls_dir.exists():
            json_files = glob.glob(
                str(release_urls_dir / "**" / "release_urls.json"), recursive=True
            )

            if json_files:
                print(f"\n📦 Processing {len(json_files)} new build artifacts...")

                for json_file in json_files:
                    with open(json_file, "r") as f:
                        data = json.load(f)

                    for asset in data.get("assets", []):
                        filename = asset["file"]

                        # Filter by dist and arch (DEB naming: package_version_arch.deb)
                        if filename.endswith(".deb") and f"_{args.arch}.deb" in filename:
                            print(f"  Processing: {filename}")

                            try:
                                metadata = get_deb_metadata(asset["url"], cache_dir)
                                all_packages.append(metadata)
                                new_packages_count += 1
                            except Exception as e:
                                print(f"  ⚠️  Error processing {filename}: {e}")
                                continue

                print(f"✓ Added {new_packages_count} new packages from current build")
            else:
                print("ℹ️  No release_urls.json files found in current build")
        else:
            print("ℹ️  Release URLs directory not found, using only GitHub releases")
    else:
        print("ℹ️  No release_urls_dir provided, using only existing GitHub releases")

    # STEP 3: Deduplicate packages (keep newest versions)
    print("\n🔄 Deduplicating packages...")
    print(f"Before deduplication: {len(all_packages)} packages")
    packages = deduplicate_packages(all_packages)
    print(f"After deduplication: {len(packages)} packages")

    if not packages:
        print(f"\n⚠️  No DEB packages found for {args.dist}/{args.arch}")
        print("Skipping metadata generation")
        sys.exit(0)

    print(f"\n📝 Generating metadata for {len(packages)} packages...")

    # Create Packages and Packages.gz
    create_packages_file(packages, packages_dir)

    # Create Release file
    create_release_file(codename, args.arch, packages_dir)

    print(f"\nAPT metadata generated successfully in {output_dir}/dists/{codename}")
    print("Note: Sign Release file with GPG to create InRelease and Release.gpg")


if __name__ == "__main__":
    main()
