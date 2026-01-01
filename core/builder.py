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
            with open(local_tar, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        click.echo(f"Extracting binaries {binaries_to_find} from {local_tar}...")
        
        extracted_dirs = set()
        with tarfile.open(local_tar, "r:gz") as tar:
            members = tar.getmembers()
            for b_name in binaries_to_find:
                member_to_extract = None
                for member in members:
                    if member.name.endswith(f"/{b_name}") or member.name == b_name:
                        member_to_extract = member
                        break
                
                if member_to_extract:
                    tar.extract(member_to_extract, path=output_dir)
                    extracted_path = os.path.join(output_dir, member_to_extract.name)
                    final_path = os.path.join(output_dir, b_name)
                    
                    if extracted_path != final_path:
                        shutil.move(extracted_path, final_path)
                    
                    # Track top-level dir to cleanup
                    parts = member_to_extract.name.split('/')
                    if len(parts) > 1:
                        extracted_dirs.add(parts[0])
                    
                    # Make executable
                    os.chmod(final_path, 0o755)
                    found_binaries.append(b_name)
                    click.echo(f"Binary ready at: {final_path}")
                else:
                    click.echo(f"Warning: Binary '{b_name}' not found in archive.")

        # Cleanup top-level extracted directories
        for d in extracted_dirs:
            dir_to_remove = os.path.join(output_dir, d)
            if os.path.isdir(dir_to_remove):
                shutil.rmtree(dir_to_remove, ignore_errors=True)

        if not found_binaries:
            click.echo("Error: No binaries found in archive.", err=True)
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
        
        # Always download and extract upstream binaries on the host
        # This avoids using 'tar' inside emulated containers which can fail (QEMU/EL10 issues)
        download_and_extract(data, output_dir, arch)

        # Generate RPM Spec
        artifacts = data.get('artifacts', {})
        if artifacts.get('rpm', {}).get('enabled'):
            # Copy extra files to build dir
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
        if not isinstance(e, click.Abort):
            click.echo(f"Error processing manifest: {e}", err=True)
        raise e

if __name__ == '__main__':
    build()
