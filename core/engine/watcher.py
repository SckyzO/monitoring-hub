import glob
import os

import click
import requests
import yaml
from marshmallow import ValidationError
from packaging.version import parse as parse_version
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.config.settings import EXPORTERS_DIR
from core.engine.schema import ManifestSchema


def load_manifest(path):
    with open(path) as f:
        data = yaml.safe_load(f)

    schema = ManifestSchema()
    try:
        return schema.load(data)
    except ValidationError as err:
        click.echo(f"Validation error in {path}: {err.messages}", err=True)
        raise click.Abort() from err


def save_manifest(path, data):
    # Ensure version is stored as string
    if "version" in data:
        data["version"] = str(data["version"])
    with open(path, "w") as f:
        yaml.dump(data, f, sort_keys=False, default_flow_style=False)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def get_latest_github_release(repo_name, token=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("tag_name")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error fetching release for {repo_name}: {e}", err=True)
        return None


@click.command()
@click.option(
    "--update/--no-update", default=False, help="Update manifest files in place"
)
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API Token")
def watch(update, token):
    """
    Scan manifests and check for upstream updates.
    """
    manifests = glob.glob(f"{EXPORTERS_DIR}/*/manifest.yaml")
    updates_found = False
    updated_exporters = []

    for manifest_path in manifests:
        try:
            data = load_manifest(manifest_path)
            name = data.get("name")
            current_version = str(data.get("version"))  # Ensure string
            upstream = data.get("upstream", {})

            if upstream.get("type") != "github":
                continue

            repo = upstream.get("repo")
            click.echo(f"Checking {name} ({current_version}) against {repo}...")

            latest_tag = get_latest_github_release(repo, token)
            if not latest_tag:
                continue

            # Compare using semantic versioning, but KEEP original tag for the manifest
            if parse_version(latest_tag) > parse_version(current_version):
                click.secho(
                    f"  -> New version available: {latest_tag} (Current: {current_version})",
                    fg="green",
                )
                updates_found = True

                if update:
                    click.echo(f"  -> Updating {manifest_path}...")
                    data["version"] = latest_tag
                    save_manifest(manifest_path, data)
                    updated_exporters.append(name)
                    click.echo("  -> Updated.")
            else:
                click.echo("  -> Up to date.")

        except Exception as e:
            click.echo(f"Error processing {manifest_path}: {e}", err=True)

    if updates_found and update:
        click.echo("Updates applied.")
        if updated_exporters:
            names_str = ", ".join(sorted(updated_exporters))
            github_output = os.environ.get("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as f:
                    f.write(f"updated_names={names_str}\\n")
    elif updates_found:
        click.echo("Updates available. Run with --update to apply.")
    else:
        click.echo("All exporters are up to date.")


if __name__ == "__main__":
    watch()
