import glob
import os

import click
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.config.settings import (
    CORE_VERSION,
    EXPORTERS_DIR,
    PORTAL_VERSION,
    SUPPORTED_DEB_DISTROS,
    SUPPORTED_DISTROS,
    TEMPLATES_DIR,
)


@click.command()
@click.option("--output", "-o", help="Output HTML file", default="index.html")
@click.option("--repo-dir", "-r", help="Path to repo root", default=".")
def generate(output, repo_dir):
    """
    Generate the portal with reality check and build status.
    """
    manifests = glob.glob(f"{EXPORTERS_DIR}/*/manifest.yaml")
    exporters_data = []

    for manifest_path in manifests:
        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)

                data["version"] = data["version"].lstrip("v")

                # Read README.md content if exists
                readme_path = os.path.join(os.path.dirname(manifest_path), "README.md")
                if os.path.exists(readme_path):
                    with open(readme_path) as r:
                        data["readme"] = r.read()
                else:
                    data["readme"] = "No documentation available."

                # RPM Availability Tracking (GitHub Releases)
                data["availability"] = {}
                rpm_targets = (
                    data.get("artifacts", {}).get("rpm", {}).get("targets", [])
                )

                for dist in SUPPORTED_DISTROS:
                    data["availability"][dist] = {}
                    for arch in ["x86_64", "aarch64"]:
                        version = data["version"]
                        rpm_name = data["name"]

                        # Construct GitHub Releases download URL
                        # Format: https://github.com/SckyzO/monitoring-hub/releases/download/v{version}/{name}-{version}-1.{dist}.{arch}.rpm
                        github_url = f"https://github.com/SckyzO/monitoring-hub/releases/download/v{version}/{rpm_name}-{version}-1.{dist}.{arch}.rpm"

                        if dist in rpm_targets:
                            # Assume success if dist is targeted (packages are on GitHub Releases)
                            data["availability"][dist][arch] = {
                                "status": "success",
                                "path": github_url,
                            }
                        else:
                            data["availability"][dist][arch] = {
                                "status": "na",
                                "path": None,
                            }

                # DEB Availability Tracking (GitHub Releases)
                deb_targets = (
                    data.get("artifacts", {}).get("deb", {}).get("targets", [])
                )
                data["deb_availability"] = {}

                for dist in SUPPORTED_DEB_DISTROS:
                    data["deb_availability"][dist] = {}
                    for arch in ["amd64", "arm64"]:
                        # DEB package names use dashes instead of underscores
                        deb_name = data["name"].replace("_", "-")
                        version = data["version"]

                        # Construct GitHub Releases download URL
                        # Format: https://github.com/SckyzO/monitoring-hub/releases/download/v{version}/{name}_{version}-1_{arch}.deb
                        github_url = f"https://github.com/SckyzO/monitoring-hub/releases/download/v{version}/{deb_name}_{version}-1_{arch}.deb"

                        if dist in deb_targets:
                            # Assume success if dist is targeted (packages are on GitHub Releases)
                            data["deb_availability"][dist][arch] = {
                                "status": "success",
                                "path": github_url,
                            }
                        else:
                            data["deb_availability"][dist][arch] = {
                                "status": "na",
                                "path": None,
                            }

                # Aggregate Build Statuses
                rpm_enabled = (
                    data.get("artifacts", {}).get("rpm", {}).get("enabled", True)
                )
                if rpm_enabled:
                    # Success only if ALL targeted distributions have at least one arch successful
                    targets = (
                        data.get("artifacts", {}).get("rpm", {}).get("targets", [])
                    )
                    failed_targets = [
                        t
                        for t in targets
                        if not any(
                            data["availability"].get(t, {}).get(a, {}).get("status")
                            == "success"
                            for a in ["x86_64", "aarch64"]
                        )
                    ]
                    data["rpm_status"] = "failed" if failed_targets else "success"
                else:
                    data["rpm_status"] = "na"

                # DEB Status
                deb_enabled = (
                    data.get("artifacts", {}).get("deb", {}).get("enabled", False)
                )
                if deb_enabled:
                    targets = (
                        data.get("artifacts", {}).get("deb", {}).get("targets", [])
                    )
                    failed_targets = [
                        t
                        for t in targets
                        if not any(
                            data["deb_availability"].get(t, {}).get(a, {}).get("status")
                            == "success"
                            for a in ["amd64", "arm64"]
                        )
                    ]
                    data["deb_status"] = "failed" if failed_targets else "success"
                else:
                    data["deb_status"] = "na"

                data["docker_status"] = (
                    "success"
                    if data.get("artifacts", {}).get("docker", {}).get("enabled", False)
                    else "na"
                )

                exporters_data.append(data)
        except Exception as e:
            print(f"Error: {e}")

    exporters_data.sort(key=lambda x: x["name"])

    # Collect unique categories dynamically
    categories = sorted({e.get("category", "System") for e in exporters_data})

    # Pre-serialize to JSON for the template
    import json

    exporters_json = json.dumps(exporters_data)
    categories_json = json.dumps(categories)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html.j2")
    rendered = template.render(
        exporters=exporters_data,
        exporters_json=exporters_json,
        categories_json=categories_json,
        core_version=CORE_VERSION,
        portal_version=PORTAL_VERSION,
    )

    with open(output, "w") as f:
        f.write(rendered)
    click.echo(f"Portal generated at {output}")

    # Generate Machine Readable Catalog
    import json

    json_output = os.path.join(os.path.dirname(output), "catalog.json")
    with open(json_output, "w") as f:
        json.dump({"exporters": exporters_data}, f, indent=2)
    click.echo(f"Catalog generated at {json_output}")


if __name__ == "__main__":
    generate()
