import gzip
import os
import shutil
import tarfile

import click
import requests
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape
from marshmallow import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.config.settings import ARCH_MAP, SUPPORTED_ARCHITECTURES, TEMPLATES_DIR
from core.engine.schema import ManifestSchema


def load_manifest(path):
    """
    Loads and validates the manifest YAML file against the strict schema.
    This ensures we fail early if the user input is invalid.
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    schema = ManifestSchema()
    try:
        return schema.load(data)
    except ValidationError as err:
        click.echo(f"Validation error in {path}: {err.messages}", err=True)
        raise click.Abort() from err


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException, OSError)),
    reraise=True,
)
def download_and_extract(data, output_dir, arch):
    """
    Downloads the upstream binary release and extracts it.

    This function handles the complexity of GitHub release naming conventions:
    1. Some projects use 'v' prefixes in tags but not in filenames.
    2. Some projects use dashes, others dots.
    3. We support custom 'archive_name' patterns to handle any edge case.
    4. Supports .tar.gz archives and simple .gz compressed binaries.
    """
    name = data["name"]
    version = data["version"]
    repo = data["upstream"]["repo"]
    binary_name = data["build"]["binary_name"]
    archive_pattern = data["upstream"].get("archive_name")

    # We strip the 'v' prefix for filename construction because Go projects
    # typically tag 'v1.0.0' but release 'project-1.0.0.tar.gz'.
    clean_version = version.lstrip("v") if version.startswith("v") else version

    # Construct the download URL
    if archive_pattern:
        # Support two formats:
        # 1. String pattern: "project-{version}-{arch}.tar.gz"
        # 2. Dict per arch: { amd64: "project-x86.tar.gz", arm64: "project-arm.tar.gz" }
        if isinstance(archive_pattern, dict):
            # Dict format: lookup the pattern for this specific architecture
            if arch not in archive_pattern:
                click.echo(
                    f"Error: No archive_name defined for architecture '{arch}' in manifest",
                    err=True,
                )
                raise click.Abort()
            pattern = archive_pattern[arch]
        else:
            # String format: use the pattern with variable substitution
            pattern = archive_pattern

        # Apply variable substitution
        filename = pattern.format(
            name=name,
            version=version,
            clean_version=clean_version,
            arch=arch,
            rpm_arch="x86_64" if arch == "amd64" else "aarch64",
            deb_arch=arch,  # DEB uses standard names (amd64, arm64)
            upstream_linux_arch="x86_64"
            if arch == "amd64"
            else "arm64",  # Mixed convention (x86_64, arm64)
        )
    else:
        # Default standard Prometheus naming convention
        upstream_arch = f"linux-{arch}"
        filename = f"{name}-{clean_version}.{upstream_arch}.tar.gz"

    url = f"https://github.com/{repo}/releases/download/{version}/{filename}"

    click.echo(f"Downloading {url}...")
    local_file = os.path.join(output_dir, filename)

    # We look for the main binary AND any extra binaries (like promtool)
    binaries_to_find = [binary_name] + data["build"].get("extra_binaries", [])
    found_binaries = []

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Case 1: Simple .gz file (single binary)
        if filename.endswith(".gz") and not filename.endswith(".tar.gz"):
            click.echo(f"Decompressing single binary {filename}...")
            final_path = os.path.join(output_dir, binary_name)
            with gzip.open(local_file, "rb") as f_in, open(final_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.chmod(final_path, 0o755)  # nosec B103 - Executable binary requires execute permissions
            found_binaries.append(binary_name)
            click.echo(f"Binary ready: {final_path}")

        # Case 2: .tar.gz archive
        else:
            click.echo(f"Extracting binaries {binaries_to_find}...")
            # We need to track extracted dirs to clean them up later
            extracted_dirs = set()
            with tarfile.open(local_file, "r:gz") as tar:
                members = tar.getmembers()
                for b_name in binaries_to_find:
                    member_to_extract = None
                    # Search for the binary, even if nested in a subfolder
                    for member in members:
                        if member.name.endswith(f"/{b_name}") or member.name == b_name:
                            member_to_extract = member
                            break

                    if member_to_extract:
                        # Flatten: we extract everything to the root of output_dir
                        tar.extract(member_to_extract, path=output_dir, filter="data")
                        extracted_path = os.path.join(
                            output_dir, member_to_extract.name
                        )
                        final_path = os.path.join(output_dir, b_name)

                        if extracted_path != final_path:
                            shutil.move(extracted_path, final_path)

                        parts = member_to_extract.name.split("/")
                        if len(parts) > 1:
                            extracted_dirs.add(parts[0])

                        os.chmod(final_path, 0o755)  # nosec B103 - Executable binary requires execute permissions
                        found_binaries.append(b_name)
                        click.echo(f"Binary ready: {final_path}")
                    else:
                        click.echo(f"Warning: Binary '{b_name}' not found.")

            # Clean up the folder structure from the tarball (we keep only binaries)
            for d in extracted_dirs:
                dir_to_remove = os.path.join(output_dir, d)
                if os.path.isdir(dir_to_remove):
                    shutil.rmtree(dir_to_remove, ignore_errors=True)

        if not found_binaries:
            click.echo(
                f"Error: No binaries found in archive. Expected binaries: {', '.join(binaries_to_find)}",
                err=True,
            )
            click.echo(
                "Hint: Check that the 'binary_name' in your manifest matches the actual binary name in the upstream release.",
                err=True,
            )
            raise click.Abort()

    except Exception as e:
        click.echo(f"Failed to process artifact: {e}", err=True)
        raise e
    finally:
        if os.path.exists(local_file):
            os.remove(local_file)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    reraise=True,
)
def download_extra_sources(data, output_dir):
    """
    Download additional files (like config examples) that are not in the release tarball.
    """
    extra_sources = data.get("build", {}).get("extra_sources", [])
    for source in extra_sources:
        url = source["url"]
        filename = source["filename"]
        click.echo(f"Downloading extra source: {url}...")
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(os.path.join(output_dir, filename), "wb") as f:
                f.write(r.content)
            click.echo(f"Extra source saved as {filename}")
        except Exception as e:
            click.echo(f"Warning: Failed to download extra source {url}: {e}")


def copy_local_binary(data, output_dir, manifest_dir):
    """
    Copy local binary or archive to output directory.
    Mirrors the "Smart Copy Logic" pattern used for extra_files.

    Args:
        data: Manifest data
        output_dir: Build output directory
        manifest_dir: Directory containing the manifest (for relative paths)
    """
    binary_name = data["build"]["binary_name"]
    local_binary = data["upstream"].get("local_binary")
    local_archive = data["upstream"].get("local_archive")
    binaries_to_find = [binary_name] + data["build"].get("extra_binaries", [])
    found_binaries = []

    if local_binary:
        # Case 1: Direct binary file
        source_path = os.path.join(manifest_dir, local_binary)

        if not os.path.exists(source_path):
            abs_path = os.path.abspath(source_path)
            click.echo(
                f"Error: Local binary not found: {source_path}",
                err=True,
            )
            click.echo(f"Absolute path checked: {abs_path}", err=True)
            click.echo(
                "Hint: Verify the 'upstream.local_binary' path in your manifest.yaml is relative to the exporter directory.",
                err=True,
            )
            raise click.Abort()

        if not os.path.isfile(source_path):
            click.echo(
                f"Error: Path is not a file: {source_path} (is it a directory?)",
                err=True,
            )
            raise click.Abort()

        click.echo(f"Copying local binary: {source_path}")
        dest_path = os.path.join(output_dir, binary_name)
        shutil.copy(source_path, dest_path)
        os.chmod(dest_path, 0o755)  # nosec B103 - Executable binary requires execute permissions
        found_binaries.append(binary_name)
        click.echo(f"Binary ready: {dest_path}")

    elif local_archive:
        # Case 2: Archive (.tar.gz or .gz)
        source_path = os.path.join(manifest_dir, local_archive)

        if not os.path.exists(source_path):
            click.echo(f"Error: Local archive not found: {source_path}", err=True)
            raise click.Abort()

        click.echo(f"Extracting local archive: {source_path}")

        if source_path.endswith(".gz") and not source_path.endswith(".tar.gz"):
            # Simple .gz file (single binary)
            click.echo("Decompressing single binary...")
            final_path = os.path.join(output_dir, binary_name)
            with gzip.open(source_path, "rb") as f_in, open(final_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            os.chmod(final_path, 0o755)  # nosec B103 - Executable binary requires execute permissions
            found_binaries.append(binary_name)
            click.echo(f"Binary ready: {final_path}")

        elif source_path.endswith(".tar.gz"):
            # .tar.gz archive - reuse existing logic from download_and_extract
            click.echo(f"Extracting binaries {binaries_to_find}...")
            extracted_dirs = set()
            with tarfile.open(source_path, "r:gz") as tar:
                members = tar.getmembers()
                for b_name in binaries_to_find:
                    member_to_extract = None
                    for member in members:
                        if member.name.endswith(f"/{b_name}") or member.name == b_name:
                            member_to_extract = member
                            break

                    if member_to_extract:
                        tar.extract(member_to_extract, path=output_dir, filter="data")
                        extracted_path = os.path.join(
                            output_dir, member_to_extract.name
                        )
                        final_path = os.path.join(output_dir, b_name)

                        if extracted_path != final_path:
                            shutil.move(extracted_path, final_path)

                        parts = member_to_extract.name.split("/")
                        if len(parts) > 1:
                            extracted_dirs.add(parts[0])

                        os.chmod(final_path, 0o755)  # nosec B103 - Executable binary requires execute permissions
                        found_binaries.append(b_name)
                        click.echo(f"Binary ready: {final_path}")
                    else:
                        click.echo(f"Warning: Binary '{b_name}' not found in archive.")

            # Cleanup extracted directories
            for d in extracted_dirs:
                dir_to_remove = os.path.join(output_dir, d)
                if os.path.isdir(dir_to_remove):
                    shutil.rmtree(dir_to_remove, ignore_errors=True)
        else:
            click.echo(f"Error: Unsupported archive format: {source_path}", err=True)
            raise click.Abort()

    if not found_binaries:
        click.echo("Error: No binaries found.", err=True)
        raise click.Abort()


def get_upstream_license(repo_slug):
    """
    Fetch license information from GitHub API.
    Returns SPDX ID (e.g. 'MIT', 'Apache-2.0') or None.
    """
    try:
        token = os.environ.get("GITHUB_TOKEN")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        url = f"https://api.github.com/repos/{repo_slug}/license"
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("license", {}).get("spdx_id")
    except Exception as e:
        click.echo(f"Warning: Could not fetch license for {repo_slug}: {e}")
    return None


def render_deb_templates(data, output_dir, arch, env, manifest_dir):
    """
    Generate the debian/ directory with all required DEB packaging files:
    - control (package metadata)
    - rules (build rules)
    - changelog (version history)
    - compat (debhelper compatibility level)
    - <name>.service (systemd unit if enabled)
    """
    from datetime import datetime

    debian_dir = os.path.join(output_dir, "debian")
    os.makedirs(debian_dir, exist_ok=True)
    click.echo(f"Creating debian/ directory at {debian_dir}")

    # Add build date for changelog (RFC 2822 format required by Debian)
    from datetime import timezone

    dt = datetime.now(timezone.utc)
    data["build_date"] = dt.strftime("%a, %d %b %Y %H:%M:%S %z")

    # Add binary_name to root level for easier access in templates
    data["binary_name"] = data.get("build", {}).get("binary_name", data["name"])

    # 0. Handle extra files FIRST (copy and set build_source before rendering templates)
    artifacts = data.get("artifacts", {})
    deb_config = artifacts.get("deb", {})
    for extra_file in deb_config.get("extra_files", []):
        source_path = extra_file["source"]
        local_src = os.path.join(manifest_dir, source_path)
        downloaded_src = os.path.join(output_dir, source_path)

        dst_name = os.path.basename(source_path)
        dst_path = os.path.join(output_dir, dst_name)

        if os.path.exists(local_src):
            shutil.copy(local_src, dst_path)
            click.echo(f"  Copied extra file: {dst_name}")
        elif os.path.exists(downloaded_src):
            if downloaded_src != dst_path:
                shutil.copy(downloaded_src, dst_path)
                click.echo(f"  Copied extra file: {dst_name}")
        else:
            click.echo(f"  Warning: Extra file {source_path} not found")

        extra_file["build_source"] = dst_name

    # 1. Generate debian/control
    template = env.get_template("debian_control.j2")
    control_content = template.render(data)
    with open(os.path.join(debian_dir, "control"), "w") as f:
        f.write(control_content)
    click.echo("  Created debian/control")

    # 2. Generate debian/rules
    template = env.get_template("debian_rules.j2")
    rules_content = template.render(data)
    rules_path = os.path.join(debian_dir, "rules")
    with open(rules_path, "w") as f:
        f.write(rules_content)
    os.chmod(rules_path, 0o755)  # nosec B103 - debian/rules must be executable
    click.echo("  Created debian/rules")

    # 3. Generate debian/changelog
    template = env.get_template("debian_changelog.j2")
    changelog_content = template.render(data)
    with open(os.path.join(debian_dir, "changelog"), "w") as f:
        f.write(changelog_content)
    click.echo("  Created debian/changelog")

    # 4. Create debian/compat (debhelper compatibility level)
    with open(os.path.join(debian_dir, "compat"), "w") as f:
        f.write("10\n")
    click.echo("  Created debian/compat")

    # 5. Generate systemd service if enabled
    if data.get("artifacts", {}).get("deb", {}).get("systemd", {}).get("enabled"):
        template = env.get_template("debian_service.j2")
        service_content = template.render(data)
        # Debian package names use dashes instead of underscores
        deb_name = data["name"].replace("_", "-")
        service_file = os.path.join(debian_dir, f"{deb_name}.service")
        with open(service_file, "w") as f:
            f.write(service_content)
        click.echo(f"  Created debian/{deb_name}.service")

    click.echo("✓ DEB packaging files generated successfully")


@click.command()
@click.option("--manifest", "-m", help="Path to manifest", required=True)
@click.option("--output-dir", "-o", help="Output directory", default="./build")
@click.option("--arch", "-a", help="Target arch", default="amd64")
def build(manifest, output_dir, arch):
    click.echo(f"Processing {manifest} ({arch})")

    # Validate architecture
    if arch not in SUPPORTED_ARCHITECTURES:
        click.echo(
            f"Error: Unsupported architecture '{arch}'. "
            f"Supported architectures: {', '.join(SUPPORTED_ARCHITECTURES)}",
            err=True,
        )
        raise click.Abort()

    try:
        data = load_manifest(manifest)
        data["arch"] = arch
        data["rpm_arch"] = ARCH_MAP.get(arch, arch)

        # License Detection Logic
        if not data.get("license"):
            detected_license = None
            if data["upstream"]["type"] == "github":
                click.echo(f"Detecting license for {data['upstream']['repo']}...")
                detected_license = get_upstream_license(data["upstream"]["repo"])

            data["license"] = (
                detected_license
                if detected_license and detected_license != "NOASSERTION"
                else "Apache-2.0"
            )
            click.echo(f"License set to: {data['license']}")

        # Setup Jinja2 with Override Logic
        template_dirs = [
            os.path.join(os.path.dirname(manifest), "templates"),
            TEMPLATES_DIR,
        ]
        env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=select_autoescape(["html", "xml", "j2"]),
        )

        os.makedirs(output_dir, exist_ok=True)

        # 1. Prepare binaries and assets
        upstream_type = data["upstream"]["type"]
        manifest_dir = os.path.dirname(os.path.abspath(manifest))

        if upstream_type == "github":
            download_and_extract(data, output_dir, arch)
        elif upstream_type == "local":
            copy_local_binary(data, output_dir, manifest_dir)
        else:
            click.echo(
                f"Error: Unknown upstream type '{upstream_type}'. "
                "Supported types: 'github', 'local'",
                err=True,
            )
            click.echo(
                "Hint: Check 'upstream.type' in your manifest.yaml",
                err=True,
            )
            raise click.Abort()

        download_extra_sources(data, output_dir)

        # Normalize version for artifacts (RPM, Docker)
        # We lstrip 'v' to respect packaging standards
        data["version"] = data["version"].lstrip("v")

        # 2. Build RPM Spec
        artifacts = data.get("artifacts", {})
        if artifacts.get("rpm", {}).get("enabled"):
            # Smart Copy Logic for sources (local assets OR downloaded sources)
            for extra_file in artifacts["rpm"].get("extra_files", []):
                source_path = extra_file["source"]
                local_src = os.path.join(os.path.dirname(manifest), source_path)
                downloaded_src = os.path.join(output_dir, source_path)

                dst_name = os.path.basename(source_path)

                if os.path.exists(local_src):
                    shutil.copy(local_src, os.path.join(output_dir, dst_name))
                elif os.path.exists(downloaded_src):
                    if downloaded_src != os.path.join(output_dir, dst_name):
                        shutil.copy(downloaded_src, os.path.join(output_dir, dst_name))
                else:
                    click.echo(f"Warning: Source file {source_path} not found.")

                extra_file["build_source"] = dst_name

            try:
                template = env.get_template(f"{data['name']}.spec.j2")
                click.echo("Using custom spec template")
            except TemplateNotFound:
                template = env.get_template("default.spec.j2")

            output_content = template.render(data)
            output_file = os.path.join(output_dir, f"{data['name']}.spec")
            with open(output_file, "w") as f:
                f.write(output_content)

        # 3. Build DEB packaging files
        if artifacts.get("deb", {}).get("enabled"):
            click.echo("\nGenerating DEB packaging files...")
            render_deb_templates(data, output_dir, arch, env, manifest_dir)

        # 4. Build Dockerfile
        if artifacts.get("docker", {}).get("enabled"):
            try:
                template = env.get_template(f"{data['name']}.Dockerfile.j2")
                click.echo("Using custom Dockerfile template")
            except TemplateNotFound:
                template = env.get_template("Dockerfile.j2")

            output_content = template.render(data)
            output_file = os.path.join(output_dir, "Dockerfile")
            with open(output_file, "w") as f:
                f.write(output_content)

    except Exception as e:
        if not isinstance(e, click.Abort):
            click.echo(f"Error: {e}", err=True)
        raise e


if __name__ == "__main__":
    build()
