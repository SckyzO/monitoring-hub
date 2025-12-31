import click
import yaml
import os
import requests
import tarfile
import shutil
from jinja2 import Environment, FileSystemLoader
from schema import ManifestSchema
from marshmallow import ValidationError

def load_manifest(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    schema = ManifestSchema()
    try:
        return schema.load(data)
    except ValidationError as err:
        click.echo(f"Validation error in {path}: {err.messages}", err=True)
        raise click.Abort()

def download_and_extract(data, output_dir):
    """
    Download the upstream release and extract the binary.
    """
    name = data['name']
    version = data['version']
    repo = data['upstream']['repo']
    binary_name = data['build']['binary_name']
    
    # Construct URL (assuming standard Prometheus release naming convention for now)
    # TODO: Make this configurable in manifest if needed
    # URL format: https://github.com/user/repo/releases/download/vX.Y.Z/name-X.Y.Z.linux-amd64.tar.gz
    filename = f"{name}-{version}.linux-amd64.tar.gz"
    url = f"https://github.com/{repo}/releases/download/v{version}/{filename}"
    
    click.echo(f"Downloading {url}...")
    
    local_tar = os.path.join(output_dir, filename)
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_tar, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        click.echo(f"Extracting {binary_name} from {local_tar}...")
        
        with tarfile.open(local_tar, "r:gz") as tar:
            # Look for the binary inside the tar (it's usually in a subdir like name-version.linux-amd64/binary)
            # We search for a file ending with the binary name
            member_to_extract = None
            for member in tar.getmembers():
                if member.name.endswith(f"/{binary_name}") or member.name == binary_name:
                    member_to_extract = member
                    break
            
            if member_to_extract:
                # Extract to a temp location then move to root of output_dir
                tar.extract(member_to_extract, path=output_dir)
                extracted_path = os.path.join(output_dir, member_to_extract.name)
                final_path = os.path.join(output_dir, binary_name)
                
                # Move to root if it was in a subdir
                if extracted_path != final_path:
                    shutil.move(extracted_path, final_path)
                    
                # Cleanup empty dirs if any
                if os.path.dirname(member_to_extract.name):
                   shutil.rmtree(os.path.join(output_dir, member_to_extract.name.split('/')[0]), ignore_errors=True)
                   
                click.echo(f"Binary ready at: {final_path}")
                
                # Make executable
                os.chmod(final_path, 0o755)
            else:
                click.echo(f"Error: Binary '{binary_name}' not found in archive.", err=True)
                raise click.Abort()

    except Exception as e:
        click.echo(f"Failed to download/extract artifact: {e}", err=True)
        raise e
    finally:
        # Clean up tarball
        if os.path.exists(local_tar):
            os.remove(local_tar)

@click.command()
@click.option('--manifest', '-m', help='Path to the manifest.yaml file', required=True)
@click.option('--output-dir', '-o', help='Directory to output generated files', default='./build')
def build(manifest, output_dir):
    """
    Build artifacts based on the provided manifest.
    """
    click.echo(f"Processing manifest: {manifest}")
    
    try:
        data = load_manifest(manifest)
        click.echo(f"Loaded and validated manifest for: {data['name']}")
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate RPM Spec
        artifacts = data.get('artifacts', {})
        if artifacts.get('rpm', {}).get('enabled'):
            template = env.get_template('default.spec.j2')
            output_content = template.render(data)
            output_file = os.path.join(output_dir, f"{data['name']}.spec")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated RPM spec: {output_file}")
            
        # Generate Dockerfile
        if artifacts.get('docker', {}).get('enabled'):
            # For Docker, we need the actual binary
            download_and_extract(data, output_dir)
            
            template = env.get_template('Dockerfile.j2')
            output_content = template.render(data)
            output_file = os.path.join(output_dir, "Dockerfile")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated Dockerfile: {output_file}")
            
    except Exception as e:
        if not isinstance(e, click.Abort):
            click.echo(f"Error processing manifest: {e}", err=True)
        raise e

if __name__ == '__main__':
    build()
