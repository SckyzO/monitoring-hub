#!/usr/bin/env python3
import click
import yaml
import requests
import shutil
import subprocess
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORTERS_DIR = PROJECT_ROOT / "exporters"
REFERENCE_FILE = PROJECT_ROOT / "manifest.reference.yaml"

def get_github_info(repo_name):
    """
    Fetches latest release info from GitHub.
    Uses 'gh' CLI if available, otherwise falls back to requests.
    """
    gh_path = shutil.which("gh")
    data = None

    if gh_path:
        try:
            click.echo(f"🔍 Fetching latest release info from {repo_name} using 'gh'...")
            cmd = [gh_path, "release", "view", "-R", repo_name, "--json", "tagName,assets"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
        except Exception as e:
            click.secho(f"⚠️ 'gh' failed: {e}. Falling back to requests...", fg="yellow")

    if not data:
        url = f"https://api.github.com/repos/{repo_name}/releases/latest"
        try:
            click.echo(f"🔍 Fetching latest release info from {repo_name} via API...")
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # Standardize 'gh' output to match API for 'tagName'
            if "tag_name" in data:
                data["tagName"] = data["tag_name"]
        except Exception as e:
            click.secho(f"⚠️ API fetch failed: {e}", fg="red")
            return None

    tag_name = data.get("tagName", "0.0.0")
    assets = data.get("assets", [])
    
    # Analyze assets
    has_amd64 = False
    has_arm64 = False
    sample_asset = None
    
    for asset in assets:
        name = asset["name"].lower()
        
        # Exclude non-linux explicitly
        if any(os_name in name for os_name in ["windows", "darwin", "macos", "freebsd", ".exe", ".dmg", ".zip"]):
            continue

        # If it says linux, good. If it says nothing but has arch, assume linux (common for go binaries)
        is_explicit_linux = "linux" in name
        
        if "amd64" in name or "x86_64" in name:
            has_amd64 = True
            if is_explicit_linux or not sample_asset:
                 sample_asset = asset["name"]
        
        if "arm64" in name or "aarch64" in name:
            has_arm64 = True
    
    archs = ["amd64"]
    if has_arm64:
        archs.append("arm64")
        
    # Try to guess archive pattern from sample asset
    archive_name = None
    if sample_asset:
        clean_version = tag_name.lstrip('v')
        
        # Heuristics for common patterns
        if f"_{clean_version}_" in sample_asset:
            archive_name = "{name}_{clean_version}_linux_{arch}.tar.gz"
        elif f"v{clean_version}" in sample_asset and "-" in sample_asset:
             archive_name = "{name}-v{clean_version}-linux-{arch}.tar.gz"
        elif f"-{clean_version}." in sample_asset:
             # Default pattern node_exporter-1.0.0.linux-amd64.tar.gz
             pass
        elif "ebpf_exporter" in sample_asset and "linux" not in sample_asset:
             # Special case for ebpf_exporter style (no linux in name) if needed
             pass

    return {
        "version": tag_name,
        "archs": archs,
        "archive_name": archive_name
    }

@click.command()
@click.option("--name", prompt="Exporter Name (e.g., node_exporter)", help="Technical name of the exporter.")
@click.option("--repo", prompt="GitHub Repository (e.g., prometheus/node_exporter)", help="Upstream GitHub repository.")
@click.option("--category", prompt="Category", type=click.Choice(['System', 'Database', 'Web', 'Network', 'Storage', 'Messaging', 'Infrastructure', 'DevOps'], case_sensitive=False), default="System", help="Portal category.")
@click.option("--description", prompt="Description", default="Prometheus exporter.", help="Short description.")
@click.option("--show-created-files", is_flag=True, help="Display the content of generated files.")
def create(name, repo, category, description, show_created_files):
    """
    Create a new exporter based on the reference manifest.
    """
    exporter_dir = EXPORTERS_DIR / name
    assets_dir = exporter_dir / "assets"
    
    if exporter_dir.exists():
        click.secho(f"❌ Error: Exporter '{name}' already exists.", fg="red")
        return

    click.echo(f"🔨 Creating '{name}'...")
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Fetch dynamic info
    gh_info = get_github_info(repo)
    
    version = "0.0.0"
    archs = ["amd64"] # Default
    archive_name = None
    
    if gh_info:
        version = gh_info["version"]
        archs = gh_info["archs"]
        archive_name = gh_info["archive_name"]
        click.secho(f"   -> Detected version: {version}", fg="blue")
        click.secho(f"   -> Detected archs: {archs}", fg="blue")
        if archive_name:
            click.secho(f"   -> Suggested pattern: {archive_name}", fg="blue")

    # Load reference manifest to use as a base structure
    try:
        with open(REFERENCE_FILE, 'r') as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        click.secho(f"⚠️ Failed to load reference manifest: {e}", fg="red")
        return

    # 1. Update Identity & Metadata
    manifest.update({
        "name": name,
        "description": description,
        "category": category,
        "version": version,
        "new": True,
        "updated": False
    })

    # 2. Update Upstream
    manifest["upstream"].update({
        "repo": repo,
        "archive_name": archive_name
    })

    # 3. Update Build
    manifest["build"].update({
        "binary_name": name,
        "archs": archs,
        # Reset optional lists to empty
        "extra_binaries": [], 
        "extra_sources": []
    })

    # 4. Update Artifacts - RPM
    manifest["artifacts"]["rpm"].update({
        "enabled": True,
        "summary": description,
        "targets": ["el8", "el9", "el10"],
        # Reset optional complex fields
        "dependencies": [],
        "extra_files": [],
        "directories": [],
        "system_user": None
    })

    # 5. Update Artifacts - Docker
    manifest["artifacts"]["docker"].update({
        "enabled": True,
        "entrypoint": [f"/usr/bin/{name}"],
        # Reset cmd
        "cmd": [],
        # Validation (Port-based by default as requested)
        "validation": {
            "enabled": True,
            "port": 9100
        }
    })
    
    # Remove keys that are explicitly None
    if manifest["artifacts"]["rpm"]["system_user"] is None:
        del manifest["artifacts"]["rpm"]["system_user"]

    manifest_path = exporter_dir / "manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f, sort_keys=False, default_flow_style=False)
    
    # Generate README
    readme_content = f"""# {name.replace('_', ' ').title()}

![Build Status](https://img.shields.io/github/actions/workflow/status/SckyzO/monitoring-hub/release.yml?label=Build)
![Version](https://img.shields.io/github/v/release/{repo}?label=Upstream)

> {description}

## 🚀 Installation

### RPM (Enterprise Linux)
```bash
sudo dnf config-manager --add-repo https://sckyzo.github.io/monitoring-hub/el9/$(arch)/ 
sudo dnf install {name}
sudo systemctl enable --now {name}
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/{name}:latest
```

## ⚙️ Configuration
See upstream documentation: [{repo}](https://github.com/{repo})
"""
    
    readme_path = exporter_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(readme_content)

    click.secho(f"\n✅ Successfully created {name}!", fg="green")
    click.echo(f"   Manifest: {manifest_path}")
    click.echo(f"   Assets:   {assets_dir}")
    
    if show_created_files:
        click.secho(f"\n--- {manifest_path.name} ---", fg="cyan")
        click.echo(yaml.dump(manifest, sort_keys=False))
        click.secho(f"\n--- {readme_path.name} ---", fg="cyan")
        click.echo(readme_content)
        click.echo("-------------------------")

    click.secho(f"\n⚠️  Please verify the detected version/archs manually:", fg="yellow")
    click.echo(f"   gh release view -R {repo} --json tagName,assets")

if __name__ == '__main__':
    create()