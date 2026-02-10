#!/usr/bin/env python3
"""
Validate artifact URLs from GitHub releases.

This script parses all exporter manifests and validates that the expected
GitHub release assets are accessible (HTTP 200).
"""

import sys
import requests
from pathlib import Path
from typing import Dict, List, Any
import yaml
import click
from urllib.parse import quote

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config.settings import EXPORTERS_DIR, ARCH_MAP


def normalize_version(version: str) -> str:
    """Remove 'v' prefix from version if present."""
    return version.lstrip("v")


def construct_archive_url(repo: str, version: str, archive_name: str, arch: str) -> str:
    """
    Construct GitHub release asset URL.

    Args:
        repo: GitHub repository (owner/repo)
        version: Release version (with or without 'v' prefix)
        archive_name: Archive name pattern with placeholders
        arch: Architecture (amd64, arm64)

    Returns:
        Full GitHub release asset URL
    """
    clean_version = normalize_version(version)
    rpm_arch = ARCH_MAP.get(arch, arch)

    # Default pattern for most exporters (matches builder.py line 77)
    if archive_name == "default" or not archive_name:
        name = repo.split("/")[-1]
        archive_name = f"{name}-{clean_version}.linux-{arch}.tar.gz"

    # Replace placeholders
    replacements = {
        "{name}": repo.split("/")[-1],
        "{version}": version,
        "{clean_version}": clean_version,
        "{arch}": arch,
        "{rpm_arch}": rpm_arch,
    }

    for placeholder, value in replacements.items():
        archive_name = archive_name.replace(placeholder, value)

    # Construct URL
    base_url = f"https://github.com/{repo}/releases/download/{version}"
    return f"{base_url}/{quote(archive_name)}"


def validate_url(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Validate URL accessibility with HTTP HEAD request.

    Args:
        url: URL to validate
        timeout: Request timeout in seconds

    Returns:
        Dictionary with status, status_code, and error info
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return {
            "status": "success" if response.status_code == 200 else "failed",
            "status_code": response.status_code,
            "url": url,
        }
    except requests.exceptions.Timeout:
        return {"status": "error", "error": "timeout", "url": url}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e), "url": url}


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse YAML manifest."""
    with open(manifest_path, "r") as f:
        return yaml.safe_load(f)


def validate_exporter(manifest_path: Path, architectures: List[str]) -> Dict[str, Any]:
    """
    Validate URLs for a single exporter.

    Args:
        manifest_path: Path to manifest.yaml
        architectures: List of architectures to test

    Returns:
        Dictionary with validation results
    """
    try:
        data = load_manifest(manifest_path)
        name = data.get("name")
        upstream = data.get("upstream", {})

        # Skip local sources
        if upstream.get("type") == "local":
            return {
                "name": name,
                "status": "skipped",
                "reason": "local source (no upstream URL)",
            }

        repo = upstream.get("repo")
        if not repo:
            return {
                "name": name,
                "status": "error",
                "reason": "missing upstream.repo",
            }

        version = data.get("version")
        if not version:
            return {"name": name, "status": "error", "reason": "missing version"}

        archive_name = upstream.get("archive_name", "default")

        # Test URLs for each architecture
        results = []
        for arch in architectures:
            url = construct_archive_url(repo, version, archive_name, arch)
            validation = validate_url(url)
            results.append({**validation, "arch": arch})

        # Determine overall status
        statuses = [r["status"] for r in results]
        if all(s == "success" for s in statuses):
            overall_status = "success"
        elif all(s in ["error", "failed"] for s in statuses):
            overall_status = "failed"
        else:
            overall_status = "partial"

        return {
            "name": name,
            "status": overall_status,
            "version": version,
            "repo": repo,
            "results": results,
        }

    except yaml.YAMLError as e:
        return {
            "name": manifest_path.parent.name,
            "status": "error",
            "reason": f"YAML parse error: {e}",
        }
    except Exception as e:
        return {
            "name": manifest_path.parent.name,
            "status": "error",
            "reason": f"unexpected error: {e}",
        }


@click.command()
@click.option(
    "--exporter",
    "-e",
    help="Validate specific exporter only (defaults to all)",
    default=None,
)
@click.option(
    "--arch",
    "-a",
    multiple=True,
    default=["amd64", "arm64"],
    help="Architectures to test (default: amd64, arm64)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output including successful URLs",
)
@click.option(
    "--fail-on-error",
    is_flag=True,
    help="Exit with non-zero status if any validation fails",
)
def main(exporter: str, arch: tuple, verbose: bool, fail_on_error: bool):
    """Validate artifact URLs for all exporters."""
    exporters_dir = Path(EXPORTERS_DIR)

    # Find manifests to validate
    if exporter:
        manifests = [exporters_dir / exporter / "manifest.yaml"]
        if not manifests[0].exists():
            click.secho(f"✗ Manifest not found: {manifests[0]}", fg="red")
            sys.exit(1)
    else:
        manifests = sorted(exporters_dir.glob("*/manifest.yaml"))

    if not manifests:
        click.secho("✗ No manifests found", fg="red")
        sys.exit(1)

    click.echo(f"🔍 Validating {len(manifests)} exporter(s)...\n")

    # Validate each exporter
    results = []
    for manifest_path in manifests:
        click.echo(f"Testing {manifest_path.parent.name}...", nl=False)
        result = validate_exporter(manifest_path, list(arch))
        results.append(result)

        # Print status indicator
        if result["status"] == "success":
            click.secho(" ✓", fg="green")
        elif result["status"] == "skipped":
            click.secho(" ⊘", fg="yellow")
        elif result["status"] == "partial":
            click.secho(" ⚠", fg="yellow")
        else:
            click.secho(" ✗", fg="red")

    # Print summary
    click.echo("\n" + "=" * 80)
    click.echo("SUMMARY")
    click.echo("=" * 80 + "\n")

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = sum(1 for r in results if r["status"] == "failed")
    partial_count = sum(1 for r in results if r["status"] == "partial")
    error_count = sum(1 for r in results if r["status"] == "error" and "reason" in r)
    skipped_count = sum(1 for r in results if r["status"] == "skipped")

    click.secho(f"✓ Success:  {success_count}", fg="green")
    click.secho(f"⚠ Partial:  {partial_count}", fg="yellow")
    click.secho(f"✗ Failed:   {failed_count}", fg="red")
    click.secho(f"✗ Errors:   {error_count}", fg="red")
    click.secho(f"⊘ Skipped:  {skipped_count}", fg="yellow")

    # Print detailed results
    if verbose or failed_count > 0 or partial_count > 0 or error_count > 0:
        click.echo("\n" + "=" * 80)
        click.echo("DETAILS")
        click.echo("=" * 80 + "\n")

        for result in results:
            if result["status"] == "skipped":
                if verbose:
                    click.echo(f"⊘ {result['name']}: {result['reason']}")
                continue

            if result["status"] == "error" and "reason" in result:
                click.secho(f"✗ {result['name']}: {result['reason']}", fg="red")
                continue

            # Show results for failed/partial/verbose
            if result["status"] in ["failed", "partial"] or (
                result["status"] == "success" and verbose
            ):
                status_color = {
                    "success": "green",
                    "partial": "yellow",
                    "failed": "red",
                }.get(result["status"], "white")

                click.secho(
                    f"\n{result['name']} ({result['version']})",
                    fg=status_color,
                    bold=True,
                )
                click.echo(f"  Repo: {result['repo']}")

                for arch_result in result.get("results", []):
                    arch_name = arch_result["arch"]
                    status = arch_result["status"]

                    if status == "success":
                        if verbose:
                            click.secho(
                                f"    ✓ {arch_name}: {arch_result['url']}", fg="green"
                            )
                    elif status == "failed":
                        click.secho(
                            f"    ✗ {arch_name}: HTTP {arch_result['status_code']}",
                            fg="red",
                        )
                        click.secho(f"      {arch_result['url']}", fg="red", dim=True)
                    elif status == "error":
                        click.secho(
                            f"    ✗ {arch_name}: {arch_result['error']}", fg="red"
                        )
                        click.secho(f"      {arch_result['url']}", fg="red", dim=True)

    # Exit with error if requested
    if fail_on_error and (failed_count > 0 or partial_count > 0 or error_count > 0):
        click.echo("\n❌ Validation failed")
        sys.exit(1)
    else:
        click.echo("\n✅ Validation complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
