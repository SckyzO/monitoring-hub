import click
import glob
import yaml
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.config.settings import SUPPORTED_DISTROS, EXPORTERS_DIR, TEMPLATES_DIR

@click.command()
@click.option('--output', '-o', help='Output HTML file', default='index.html')
@click.option('--repo-dir', '-r', help='Path to repo root', default='.')
def generate(output, repo_dir):
    """
    Generate the portal with reality check and build status.
    """
    manifests = glob.glob(f"{EXPORTERS_DIR}/*/manifest.yaml")
    exporters_data = []

    for manifest_path in manifests:
        try:
            with open(manifest_path, 'r') as f:
                data = yaml.safe_load(f)
                
                data['version'] = data['version'].lstrip('v')
                
                data['availability'] = {}
                rpm_targets = data.get('artifacts', {}).get('rpm', {}).get('targets', [])
                
                for dist in SUPPORTED_DISTROS:
                    data['availability'][dist] = {}
                    for arch in ['x86_64', 'aarch64']:
                        pattern = os.path.join(repo_dir, dist, arch, f"{data['name']}-*.{dist}*.{arch}.rpm")
                        found_files = glob.glob(pattern)
                        is_target = dist in rpm_targets
                        
                        if found_files:
                            data['availability'][dist][arch] = {
                                'status': 'success',
                                'path': os.path.relpath(found_files[0], repo_dir)
                            }
                        elif is_target:
                            data['availability'][dist][arch] = {'status': 'failed', 'path': None}
                        else:
                            data['availability'][dist][arch] = {'status': 'na', 'path': None}
                
                exporters_data.append(data)
        except Exception as e:
            print(f"Error: {e}")

    exporters_data.sort(key=lambda x: x['name'])
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template('index.html.j2')
    rendered = template.render(exporters=exporters_data)

    with open(output, 'w') as f:
        f.write(rendered)
    click.echo(f"Portal generated at {output}")

    # Generate Machine Readable Catalog
    import json
    json_output = os.path.join(os.path.dirname(output), 'catalog.json')
    with open(json_output, 'w') as f:
        json.dump({'exporters': exporters_data}, f, indent=2)
    click.echo(f"Catalog generated at {json_output}")

if __name__ == '__main__':
    generate()