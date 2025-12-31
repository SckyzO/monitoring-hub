import click
import glob
import yaml
import os
from jinja2 import Environment, FileSystemLoader

@click.command()
@click.option('--output', '-o', help='Output HTML file', default='index.html')
def generate(output):
    """
    Generate the static site index.html
    """
    manifests = glob.glob("exporters/*/manifest.yaml")
    exporters_data = []

    for manifest_path in manifests:
        try:
            with open(manifest_path, 'r') as f:
                data = yaml.safe_load(f)
                exporters_data.append(data)
        except Exception as e:
            print(f"Error loading {manifest_path}: {e}")

    # Sort by name
    exporters_data.sort(key=lambda x: x['name'])

    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index.html.j2')

    rendered = template.render(exporters=exporters_data)

    with open(output, 'w') as f:
        f.write(rendered)
    
    click.echo(f"Site generated at {output}")

if __name__ == '__main__':
    generate()
