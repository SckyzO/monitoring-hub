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


def load_release_urls(release_urls_dir):
    """
    Load all release_urls.json artifacts from the build.
    Returns a dict mapping (exporter, filename) -> url.
    """
    if not release_urls_dir or not os.path.exists(release_urls_dir):
        return {}

    url_map = {}
    import json

    for root, dirs, files in os.walk(release_urls_dir):
        for file in files:
            if file.endswith("release_urls.json"):
                try:
                    with open(os.path.join(root, file)) as f:
                        data = json.load(f)
                        exporter = data.get("exporter")
                        for asset in data.get("assets", []):
                            filename = asset.get("file")
                            url = asset.get("url")
                            if exporter and filename and url:
                                url_map[(exporter, filename)] = url
                except Exception as e:
                    print(f"Warning: Failed to load {file}: {e}")

    return url_map


def load_build_info(build_info_dir):
    """
    Load all build-info.json artifacts from the build.
    Returns a dict mapping exporter -> latest build_date.
    """
    if not build_info_dir or not os.path.exists(build_info_dir):
        return {}

    build_dates = {}
    import json

    for root, dirs, files in os.walk(build_info_dir):
        for file in files:
            if file.endswith("build-info.json"):
                try:
                    with open(os.path.join(root, file)) as f:
                        data = json.load(f)
                        exporter = data.get("exporter")
                        build_date = data.get("build_date")
                        if exporter and build_date:
                            # Keep the latest date if multiple builds for same exporter
                            if exporter not in build_dates or build_date > build_dates[exporter]:
                                build_dates[exporter] = build_date
                except Exception as e:
                    print(f"Warning: Failed to load {file}: {e}")

    return build_dates


@click.command()
@click.option("--output", "-o", help="Output HTML file", default="index.html")
@click.option("--repo-dir", "-r", help="Path to repo root", default=".")
@click.option(
    "--release-urls-dir",
    help="Directory containing release_urls.json artifacts from builds",
    default=None,
)
@click.option(
    "--skip-catalog",
    is_flag=True,
    help="Skip catalog.json generation (only update portal HTML)",
    default=False,
)
def generate(output, repo_dir, release_urls_dir, skip_catalog):
    """
    Generate the portal with reality check and build status.
    """
    # Load real availability from release_urls artifacts
    release_url_map = load_release_urls(release_urls_dir)

    # Load build dates from artifacts
    build_dates = load_build_info(release_urls_dir)

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
                        filename = f"{rpm_name}-{version}-1.{dist}.{arch}.rpm"

                        # Check if package was actually uploaded (using release_urls artifacts)
                        real_url = release_url_map.get((rpm_name, filename))

                        if real_url:
                            # Package was uploaded successfully
                            data["availability"][dist][arch] = {
                                "status": "success",
                                "path": real_url,
                            }
                        elif dist in rpm_targets:
                            # Targeted but not uploaded yet (build may be in progress or failed)
                            # Generate expected URL as fallback (tag format: exporter-vVersion)
                            tag = f"{rpm_name}-v{version}"
                            github_url = f"https://github.com/SckyzO/monitoring-hub/releases/download/{tag}/{filename}"
                            data["availability"][dist][arch] = {
                                "status": "pending",
                                "path": github_url,
                            }
                        else:
                            # Not a target
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
                        filename = f"{deb_name}_{version}-1_{arch}.deb"

                        # Check if package was actually uploaded (using release_urls artifacts)
                        real_url = release_url_map.get((data["name"], filename))

                        if real_url:
                            # Package was uploaded successfully
                            data["deb_availability"][dist][arch] = {
                                "status": "success",
                                "path": real_url,
                            }
                        elif dist in deb_targets:
                            # Targeted but not uploaded yet (build may be in progress or failed)
                            # Generate expected URL as fallback (tag format: exporter-vVersion)
                            tag = f"{data['name']}-v{version}"
                            github_url = f"https://github.com/SckyzO/monitoring-hub/releases/download/{tag}/{filename}"
                            data["deb_availability"][dist][arch] = {
                                "status": "pending",
                                "path": github_url,
                            }
                        else:
                            # Not a target
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
                    failed_targets = []
                    pending_targets = []

                    for t in targets:
                        has_success = any(
                            data["availability"].get(t, {}).get(a, {}).get("status")
                            == "success"
                            for a in ["x86_64", "aarch64"]
                        )
                        has_pending = any(
                            data["availability"].get(t, {}).get(a, {}).get("status")
                            == "pending"
                            for a in ["x86_64", "aarch64"]
                        )

                        if not has_success:
                            if has_pending:
                                pending_targets.append(t)
                            else:
                                failed_targets.append(t)

                    if failed_targets:
                        data["rpm_status"] = "failed"
                    elif pending_targets:
                        data["rpm_status"] = "pending"
                    else:
                        data["rpm_status"] = "success"
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
                    failed_targets = []
                    pending_targets = []

                    for t in targets:
                        has_success = any(
                            data["deb_availability"].get(t, {}).get(a, {}).get("status")
                            == "success"
                            for a in ["amd64", "arm64"]
                        )
                        has_pending = any(
                            data["deb_availability"].get(t, {}).get(a, {}).get("status")
                            == "pending"
                            for a in ["amd64", "arm64"]
                        )

                        if not has_success:
                            if has_pending:
                                pending_targets.append(t)
                            else:
                                failed_targets.append(t)

                    if failed_targets:
                        data["deb_status"] = "failed"
                    elif pending_targets:
                        data["deb_status"] = "pending"
                    else:
                        data["deb_status"] = "success"
                else:
                    data["deb_status"] = "na"

                data["docker_status"] = (
                    "success"
                    if data.get("artifacts", {}).get("docker", {}).get("enabled", False)
                    else "na"
                )

                # Add build date from artifacts
                data["build_date"] = build_dates.get(data["name"])

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

    # Generate Machine Readable Catalog (unless skipped)
    if not skip_catalog:
        import json

        json_output = os.path.join(os.path.dirname(output), "catalog.json")
        with open(json_output, "w") as f:
            json.dump({"exporters": exporters_data}, f, indent=2)
        click.echo(f"Catalog generated at {json_output}")
    else:
        click.echo("Catalog generation skipped (--skip-catalog)")


if __name__ == "__main__":
    generate()
