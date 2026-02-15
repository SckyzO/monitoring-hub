#!/usr/bin/env python3
"""
Site generator V2 - Uses granular catalog structure.

This version reads atomic artifact JSONs from catalog/<exporter>/*.json
and aggregates them using aggregate_catalog_metadata.py.

Usage:
    python3 -m core.engine.site_generator_v2 --output index.html --catalog-dir catalog
"""

import glob
import json
import os
import subprocess
from pathlib import Path

import click
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config.settings import (
    CORE_VERSION,
    EXPORTERS_DIR,
    PORTAL_VERSION,
    TEMPLATES_DIR,
)


def load_or_aggregate_metadata(exporter_name, catalog_dir, manifest_path):
    """
    Load exporter metadata.json, or aggregate it from granular artifacts if missing.

    Returns dict with exporter metadata, or None if no data available.
    """
    exporter_dir = Path(catalog_dir) / exporter_name
    metadata_file = exporter_dir / "metadata.json"

    # If metadata.json exists and is recent, use it
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)

                # Validate format version
                if metadata.get("format_version") == "3.0":
                    return metadata
                else:
                    print(
                        f"Warning: Old format in {metadata_file}, regenerating..."
                    )
        except Exception as e:
            print(f"Warning: Failed to load {metadata_file}: {e}")

    # Aggregate from granular artifacts
    if not exporter_dir.exists() or not list(exporter_dir.glob("*.json")):
        # No artifacts yet, return placeholder
        return None

    print(f"Aggregating metadata for {exporter_name}...")

    try:
        subprocess.run(
            [
                "python3",
                "core/scripts/aggregate_catalog_metadata.py",
                "--exporter",
                exporter_name,
                "--catalog-dir",
                catalog_dir,
                "--manifest-path",
                manifest_path,
                "--output",
                str(metadata_file),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Load newly generated metadata
        with open(metadata_file) as f:
            return json.load(f)

    except subprocess.CalledProcessError as e:
        print(f"Error aggregating metadata for {exporter_name}: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error aggregating metadata for {exporter_name}: {e}")
        return None


def convert_metadata_to_legacy_format(metadata, manifest):
    """
    Convert V3 metadata format to legacy format expected by portal template.

    This maintains backward compatibility with existing index.html.j2 template.
    """
    if not metadata:
        # No metadata, use manifest only
        return {
            "name": manifest.get("name"),
            "version": manifest.get("version", "").lstrip("v"),
            "category": manifest.get("category", "System"),
            "description": manifest.get("description", ""),
            "readme": manifest.get("readme", "No documentation available."),
            "build_date": None,
            "availability": {},
            "deb_availability": {},
            "rpm_status": "na",
            "deb_status": "na",
            "docker_status": "na",
        }

    # Convert V3 artifacts to legacy availability format
    rpm_availability = {}
    for dist, archs in metadata.get("artifacts", {}).get("rpm", {}).items():
        rpm_availability[dist] = {}
        for arch, info in archs.items():
            # Map amd64/arm64 to x86_64/aarch64 for RPM
            rpm_arch = "x86_64" if arch == "amd64" else "aarch64" if arch == "arm64" else arch
            rpm_availability[dist][rpm_arch] = {
                "status": info.get("status", "na"),
                "path": info.get("url"),
            }

    deb_availability = {}
    for dist, archs in metadata.get("artifacts", {}).get("deb", {}).items():
        deb_availability[dist] = {}
        for arch, info in archs.items():
            deb_availability[dist][arch] = {
                "status": info.get("status", "na"),
                "path": info.get("url"),
            }

    return {
        "name": metadata.get("exporter"),
        "version": metadata.get("version"),
        "category": metadata.get("category", "System"),
        "description": metadata.get("description", ""),
        "readme": manifest.get("readme", "No documentation available."),
        "build_date": metadata.get("last_updated"),
        "availability": rpm_availability,
        "deb_availability": deb_availability,
        "rpm_status": metadata.get("status", {}).get("rpm", "na"),
        "deb_status": metadata.get("status", {}).get("deb", "na"),
        "docker_status": metadata.get("status", {}).get("docker", "na"),
    }


def load_security_stats(repo_dir):
    """
    Load security statistics from security-stats.json.
    Returns the security stats dict, or empty stats if not found.
    """
    stats_path = os.path.join(repo_dir, "security-stats.json")

    if not os.path.exists(stats_path):
        return {
            "total_vulnerabilities": 0,
            "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "top_exporters": [],
            "scan_date": None,
            "total_exporters_scanned": 0,
        }

    try:
        with open(stats_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load security stats: {e}")
        return {
            "total_vulnerabilities": 0,
            "by_severity": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "top_exporters": [],
            "scan_date": None,
            "total_exporters_scanned": 0,
        }


@click.command()
@click.option("--output", "-o", help="Output HTML file", default="index.html")
@click.option("--repo-dir", "-r", help="Path to repo root", default=".")
@click.option(
    "--catalog-dir",
    help="Catalog directory (contains granular artifacts)",
    default="catalog",
)
@click.option(
    "--skip-catalog",
    is_flag=True,
    help="Skip catalog.json generation (only update portal HTML)",
    default=False,
)
def generate(output, repo_dir, catalog_dir, skip_catalog):
    """
    Generate the portal using V3 granular catalog structure.
    """
    manifests = glob.glob(f"{EXPORTERS_DIR}/*/manifest.yaml")
    exporters_data = []

    print(f"Found {len(manifests)} exporters")

    for manifest_path in manifests:
        try:
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)

            exporter_name = manifest["name"]
            manifest["version"] = manifest["version"].lstrip("v")

            # Read README.md content if exists
            readme_path = os.path.join(os.path.dirname(manifest_path), "README.md")
            if os.path.exists(readme_path):
                with open(readme_path) as r:
                    manifest["readme"] = r.read()
            else:
                manifest["readme"] = "No documentation available."

            # Load or aggregate metadata from catalog
            metadata = load_or_aggregate_metadata(
                exporter_name, catalog_dir, manifest_path
            )

            # Convert to legacy format for template
            exporter_data = convert_metadata_to_legacy_format(metadata, manifest)

            exporters_data.append(exporter_data)

        except Exception as e:
            print(f"Error processing {manifest_path}: {e}")
            import traceback

            traceback.print_exc()

    exporters_data.sort(key=lambda x: x["name"])

    print(f"Loaded {len(exporters_data)} exporters")

    # Collect unique categories dynamically
    categories = sorted({e.get("category", "System") for e in exporters_data})

    # Load security statistics
    security_stats = load_security_stats(repo_dir)

    # Pre-serialize to JSON for the template
    exporters_json = json.dumps(exporters_data)
    categories_json = json.dumps(categories)
    security_stats_json = json.dumps(security_stats)

    # Render portal HTML
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html.j2")
    rendered = template.render(
        exporters=exporters_data,
        exporters_json=exporters_json,
        categories_json=categories_json,
        security_stats=security_stats,
        security_stats_json=security_stats_json,
        core_version=CORE_VERSION,
        portal_version=PORTAL_VERSION,
    )

    with open(output, "w") as f:
        f.write(rendered)

    click.echo(f"Portal generated at {output}")

    # Generate Machine Readable Catalog (unless skipped)
    if not skip_catalog:
        output_dir = os.path.dirname(output) or "."

        # Create catalog directory
        catalog_output_dir = os.path.join(output_dir, "catalog")
        os.makedirs(catalog_output_dir, exist_ok=True)

        # 1. Generate lightweight index.json
        index_data = {
            "version": "3.0",
            "exporters": [
                {
                    "name": e["name"],
                    "version": e["version"],
                    "category": e.get("category", "System"),
                    "last_updated": e.get("build_date"),
                }
                for e in exporters_data
            ],
        }

        index_output = os.path.join(catalog_output_dir, "index.json")
        with open(index_output, "w") as f:
            json.dump(index_data, f, indent=2)

        click.echo(f"✓ Catalog index generated at {index_output}")

        # 2. Copy per-exporter metadata.json files
        copied = 0
        for exporter_data in exporters_data:
            exporter_name = exporter_data["name"]
            source_file = Path(catalog_dir) / exporter_name / "metadata.json"
            dest_file = Path(catalog_output_dir) / f"{exporter_name}.json"

            if source_file.exists():
                # Copy metadata.json to catalog/<exporter>.json
                with open(source_file) as f:
                    metadata = json.load(f)

                with open(dest_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                copied += 1

        click.echo(f"✓ Copied {copied} exporter metadata files")

        # 3. Generate legacy catalog.json (for compatibility)
        legacy_output = os.path.join(output_dir, "catalog.json")
        with open(legacy_output, "w") as f:
            json.dump(
                {
                    "exporters": exporters_data,
                    "_note": "This format is deprecated. Use /catalog/index.json for new integrations.",
                },
                f,
                indent=2,
            )

        click.echo(f"✓ Legacy catalog generated at {legacy_output}")
    else:
        click.echo("Catalog generation skipped (--skip-catalog)")


if __name__ == "__main__":
    generate()
