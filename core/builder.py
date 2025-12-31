import click
import yaml
import os
from jinja2 import Environment, FileSystemLoader

@click.command()
@click.option('--manifest', '-m', help='Path to the manifest.yaml file', required=True)
@click.option('--output-dir', '-o', help='Directory to output generated files', default='./build')
def build(manifest, output_dir):
    """
    Build artifacts based on the provided manifest.
    """
    click.echo(f"Processing manifest: {manifest}")
    
    try:
        with open(manifest, 'r') as f:
            data = yaml.safe_load(f)
            
        click.echo(f"Loaded manifest for: {data.get('name', 'Unknown')}")
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate RPM Spec
        if data.get('artifacts', {}).get('rpm', {}).get('enabled'):
            template = env.get_template('default.spec.j2')
            output_content = template.render(data)
            output_file = os.path.join(output_dir, f"{data['name']}.spec")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated RPM spec: {output_file}")
            
        # Generate Dockerfile
        if data.get('artifacts', {}).get('docker', {}).get('enabled'):
            template = env.get_template('Dockerfile.j2')
            output_content = template.render(data)
            output_file = os.path.join(output_dir, "Dockerfile")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated Dockerfile: {output_file}")
            
    except Exception as e:
        click.echo(f"Error processing manifest: {e}", err=True)

if __name__ == '__main__':
    build()
