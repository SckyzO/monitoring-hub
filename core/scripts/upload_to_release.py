#!/usr/bin/env python3
"""
Upload binaries to GitHub Releases.

This script uploads RPM/DEB packages to GitHub Releases and returns
the download URLs for use in YUM/APT repository metadata.
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests


def retry_with_backoff(func, max_retries=5, initial_delay=15):
    """Retry function with exponential backoff and jitter for transient errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except (
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:
            # Network/SSL errors - always retry with longer delays
            if attempt < max_retries - 1:
                base_delay = initial_delay * (2**attempt)
                # Add jitter (±20%) to avoid thundering herd
                jitter = base_delay * 0.2 * (2 * random.random() - 1)
                delay = base_delay + jitter
                print(
                    f"Attempt {attempt + 1} failed with {type(e).__name__}, "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                print(
                    f"Max retries ({max_retries}) reached for {type(e).__name__}, "
                    "giving up"
                )
                raise
        except requests.exceptions.HTTPError as e:
            # HTTP errors - retry 404, 429, and 5xx
            if (
                e.response.status_code in [404, 429, 500, 502, 503, 504]
                and attempt < max_retries - 1
            ):
                base_delay = initial_delay * (2**attempt)
                # Add jitter (±20%) to avoid thundering herd
                jitter = base_delay * 0.2 * (2 * random.random() - 1)
                delay = base_delay + jitter
                print(
                    f"Attempt {attempt + 1} failed with HTTP {e.response.status_code}, "
                    f"retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                raise
    return None


def get_release_tag(exporter_name: str, version: str) -> str:
    """Generate release tag from exporter name and version."""
    if not version.startswith("v"):
        version = f"v{version}"
    return f"{exporter_name}-{version}"


def get_or_create_release(repo: str, tag: str, token: str, exporter_name: str) -> Dict:
    """Get existing release or create new one."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Check if release exists
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 200:
        print(f"Release {tag} already exists")
        release_data = response.json()
        # Debug info
        print(f"Release ID: {release_data.get('id', 'NOT FOUND')}")
        print(f"Upload URL: {release_data.get('upload_url', 'NOT FOUND')}")
        print(f"Assets count: {len(release_data.get('assets', []))}")

        # Verify upload_url is present and valid
        if "upload_url" not in release_data or not release_data["upload_url"]:
            print(f"Warning: Release {tag} missing upload_url, recreating...")
            # Delete and recreate
            delete_url = (
                f"https://api.github.com/repos/{repo}/releases/{release_data['id']}"
            )
            requests.delete(delete_url, headers=headers, timeout=30)
            # Continue to create new release below
        else:
            return release_data

    # Create new release
    create_url = f"https://api.github.com/repos/{repo}/releases"
    data = {
        "tag_name": tag,
        "name": f"{exporter_name} {tag}",
        "body": f"Release of {exporter_name} version {tag}\n\n"
        f"Automated build from Monitoring Hub.",
        "draft": False,
        "prerelease": False,
    }

    response = requests.post(create_url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    print(f"Created release {tag}")
    return response.json()


def get_release_by_id(repo: str, release_id: int, token: str) -> Dict:
    """Fetch fresh release data by ID to get updated assets list."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def upload_asset(release: Dict, file_path: Path, token: str, repo: str) -> Dict:
    """Upload asset to release and return download URL."""
    # Random delay (2-5s) to avoid hammering GitHub API and spread load
    time.sleep(2 + random.random() * 3)

    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/octet-stream",
    }

    file_name = file_path.name

    # Refresh release data to get current assets list
    # This is critical for handling parallel uploads correctly
    print(f"Refreshing release data to check for existing assets...")
    fresh_release = get_release_by_id(repo, release["id"], token)

    # Verify upload_url is available
    if "upload_url" not in fresh_release:
        raise ValueError(
            f"Release missing upload_url: {fresh_release.get('id', 'unknown')}"
        )

    # Check if asset already exists (using fresh data)
    existing_asset = None
    for asset in fresh_release.get("assets", []):
        if asset["name"] == file_name:
            existing_asset = asset
            break

    if existing_asset:
        file_size = file_path.stat().st_size
        existing_size = existing_asset["size"]

        # Compare sizes to detect if file is identical
        if file_size == existing_size:
            print(
                f"✓ Asset {file_name} already exists with matching size ({file_size} bytes), skipping upload"
            )
            return existing_asset
        else:
            print(
                f"⚠ Asset {file_name} exists but size differs "
                f"(local: {file_size}, remote: {existing_size}), replacing..."
            )
            delete_url = f"https://api.github.com/repos/{repo}/releases/assets/{existing_asset['id']}"
            delete_response = requests.delete(
                delete_url,
                headers={"Authorization": f"token {token}"},
                timeout=30,
            )
            if delete_response.status_code == 204:
                print(f"✓ Deleted existing asset {file_name}")
                # After deletion, refresh again to get updated upload_url
                print(f"Refreshing release data after deletion...")
                fresh_release = get_release_by_id(repo, release["id"], token)
            else:
                print(
                    f"⚠ Delete returned {delete_response.status_code}, continuing anyway..."
                )

    # Use upload_url from fresh release data (critical after deletion)
    upload_url = fresh_release["upload_url"].replace("{?name,label}", "")
    print(f"Using upload URL: {upload_url}")

    # Upload asset with retry and longer timeout
    print(f"📤 Uploading {file_name}...")

    def do_upload():
        with open(file_path, "rb") as f:
            params = {"name": file_name}
            # Use longer timeout for large files: (connect timeout, read timeout)
            response = requests.post(
                upload_url, headers=headers, params=params, data=f, timeout=(30, 600)
            )
            response.raise_for_status()
            return response.json()

    asset_data = retry_with_backoff(do_upload)  # Uses defaults: 5 retries, 15s initial
    print(f"✓ Uploaded {file_name} -> {asset_data['browser_download_url']}")
    return asset_data


def main():
    parser = argparse.ArgumentParser(description="Upload binaries to GitHub Releases")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/name)")
    parser.add_argument("--exporter", required=True, help="Exporter name")
    parser.add_argument("--version", required=True, help="Version number")
    parser.add_argument("--files", required=True, nargs="+", help="Files to upload")
    parser.add_argument(
        "--token",
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub token (or use GITHUB_TOKEN env)",
    )
    parser.add_argument(
        "--output",
        help="JSON file to write download URLs",
        default="release_urls.json",
    )

    args = parser.parse_args()

    if not args.token:
        print("Error: GitHub token required (--token or GITHUB_TOKEN env)")
        sys.exit(1)

    # Generate release tag
    tag = get_release_tag(args.exporter, args.version)

    # Get or create release
    release = get_or_create_release(args.repo, tag, args.token, args.exporter)

    # Upload all files
    print(f"\n⬆️  Uploading {len(args.files)} file(s) to release {tag}...")
    urls: List[Dict[str, str]] = []
    for idx, file_path_str in enumerate(args.files, 1):
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"⚠ Warning: {file_path} does not exist, skipping")
            continue

        print(f"\n[{idx}/{len(args.files)}] Processing {file_path.name}...")
        asset = upload_asset(release, file_path, args.token, args.repo)
        urls.append(
            {
                "file": file_path.name,
                "url": asset["browser_download_url"],
                "size": asset["size"],
            }
        )

    # Write URLs to output file
    output_data = {
        "exporter": args.exporter,
        "version": args.version,
        "tag": tag,
        "release_url": release["html_url"],
        "assets": urls,
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nUpload complete! URLs written to {args.output}")
    print(f"Release: {release['html_url']}")


if __name__ == "__main__":
    main()
