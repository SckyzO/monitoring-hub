import click
import glob
import yaml
import os
from jinja2 import Environment, FileSystemLoader

@click.command()
@click.option('--output', '-o', help='Output HTML file', default='index.html')
@click.option('--repo-dir', '-r', help='Path to the YUM repo root', default='.')
def generate(output, repo_dir):
    """
    Generate the static site index.html with reality check on existing RPMs.
    """
    manifests = glob.glob("exporters/*/manifest.yaml")
    exporters_data = []

    for manifest_path in manifests:
        try:
            with open(manifest_path, 'r') as f:
                data = yaml.safe_load(f)
                
                # Check reality for each target/arch in the built repository
                # This ensures we only show what was actually built successfully
                data['availability'] = {}
                for dist in ['el8', 'el9', 'el10']:
                    data['availability'][dist] = {}
                    for arch in ['x86_64', 'aarch64']:
                        # Pattern to match the generated RPM
                        pattern = os.path.join(repo_dir, dist, arch, f"{data['name']}-*.{dist}*.{arch}.rpm")
                        found_files = glob.glob(pattern)
                        
                        if found_files:
                            # Store the relative path to the first found RPM for direct link
                            data['availability'][dist][arch] = os.path.relpath(found_files[0], repo_dir)
                        else:
                            data['availability'][dist][arch] = None
                
                exporters_data.append(data)
        except Exception as e:
            print(f"Error processing {manifest_path}: {e}")

    # Sort by name
    exporters_data.sort(key=lambda x: x['name'])

    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index.html.j2')

    rendered = template.render(exporters=exporters_data)

    with open(output, 'w') as f:
        f.write(rendered)
    
    click.echo(f"Site generated at {output} (Checked against {repo_dir})")

if __name__ == '__main__':
    generate()