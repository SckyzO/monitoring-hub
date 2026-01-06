#!/usr/bin/env python3
import click
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORTERS_DIR = PROJECT_ROOT / "exporters"
REFERENCE_FILE = PROJECT_ROOT / "manifest.reference.yaml"

@click.command()
@click.option("--name", prompt="Exporter Name (e.g., node_exporter)", help="Technical name of the exporter.")
@click.option("--repo", prompt="GitHub Repository (e.g., prometheus/node_exporter)", help="Upstream GitHub repository.")
@click.option("--category", prompt="Category", type=click.Choice(['System', 'Database', 'Web', 'Network', 'Storage', 'Messaging', 'Infrastructure'], case_sensitive=False), default="System", help="Portal category.")
@click.option("--description", prompt="Description", default="Prometheus exporter.", help="Short description.")
def create(name, repo, category, description):
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

    # Load reference to ensure structure compliance (if possible), or use a clean dict structure
    # Here we define the clean structure based on the reference
    manifest = {
        "name": name,
        "description": description,
        "category": category,
        "version": "0.0.0",
        "new": True,
        "upstream": {
            "type": "github",
            "repo": repo,
            "strategy": "latest_release"
        },
        "build": {
            "method": "binary_repack",
            "binary_name": name
        },
        "artifacts": {
            "rpm": {
                "enabled": True,
                "targets": ["el8", "el9", "el10"],
                "service_file": True
            },
            "docker": {
                "enabled": True,
                "entrypoint": [f"/usr/bin/{name}"],
                "validation": {
                    "enabled": True,
                    "command": "--version"
                }
            }
        }
    }

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
```

### Docker
```bash
docker pull ghcr.io/sckyzo/monitoring-hub/{name}:latest
```

## ⚙️ Configuration
See upstream documentation: [{repo}](https://github.com/{repo})
"""
    
    with open(exporter_dir / "README.md", "w") as f:
        f.write(readme_content)

    click.secho(f"\n✅ Successfully created {name}!", fg="green")
    click.echo(f"   Manifest: {manifest_path}")
    click.echo(f"   Assets:   {assets_dir}")

if __name__ == '__main__':
    create()