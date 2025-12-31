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

def download_and_extract(data, output_dir, arch):
    """
    Download the upstream release and extract the binary.
    """
    name = data['name']
    version = data['version']
    repo = data['upstream']['repo']
    binary_name = data['build']['binary_name']
    
    # Map our arch names to upstream conventions if needed
    # internally we use: amd64, arm64
    # upstream uses: linux-amd64, linux-arm64
    upstream_arch = f"linux-{arch}"
    
    # Construct URL
    filename = f"{name}-{version}.{upstream_arch}.tar.gz"
    url = f"https://github.com/{repo}/releases/download/v{version}/{filename}"
    
    click.echo(f"Downloading {url}...")
    
    local_tar = os.path.join(output_dir, filename)
    binaries_to_find = [binary_name] + data['build'].get('extra_binaries', [])
    found_binaries = []
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
# ... (rest of download logic)

@click.command()
@click.option('--manifest', '-m', help='Path to the manifest.yaml file', required=True)
@click.option('--output-dir', '-o', help='Directory to output generated files', default='./build')
@click.option('--arch', '-a', help='Target architecture (amd64, arm64)', default='amd64')
def build(manifest, output_dir, arch):
    """
    Build artifacts based on the provided manifest.
    """
    click.echo(f"Processing manifest: {manifest} for arch: {arch}")
    
    try:
        data = load_manifest(manifest)
        # Inject arch into data for templates
        data['arch'] = arch
        # RPM arch name mapping (amd64 -> x86_64, arm64 -> aarch64)
        rpm_arch_map = {'amd64': 'x86_64', 'arm64': 'aarch64'}
        data['rpm_arch'] = rpm_arch_map.get(arch, arch)
        
        click.echo(f"Loaded and validated manifest for: {data['name']}")
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate RPM Spec
        artifacts = data.get('artifacts', {})
        if artifacts.get('rpm', {}).get('enabled'):
            # Only generate spec if the arch is supported (add check later if needed)
            
            # Copy extra files to build dir (only needed once per dir really, but ok)
            for extra_file in artifacts['rpm'].get('extra_files', []):
                src = os.path.join(os.path.dirname(manifest), extra_file['source'])
                dst_name = os.path.basename(extra_file['source'])
                shutil.copy(src, os.path.join(output_dir, dst_name))
                extra_file['build_source'] = dst_name

            template = env.get_template('default.spec.j2')
            output_content = template.render(data)
            # Differentiate spec file name if building multiple archs in same dir
            output_file = os.path.join(output_dir, f"{data['name']}.spec")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated RPM spec: {output_file}")
            
        # Generate Dockerfile
        if artifacts.get('docker', {}).get('enabled'):
            # For Docker, we need the actual binary
            download_and_extract(data, output_dir, arch)
            
            template = env.get_template('Dockerfile.j2')
            output_content = template.render(data)
            output_file = os.path.join(output_dir, "Dockerfile")
            with open(output_file, 'w') as f:
                f.write(output_content)
            click.echo(f"Generated Dockerfile: {output_file}")
            
    except Exception as e:

if __name__ == '__main__':
    build()
