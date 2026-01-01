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
    """
    Loads and validates the manifest YAML file against the strict schema.
    This ensures we fail early if the user input is invalid.
    """
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
    Downloads the upstream binary release and extracts it.
    
    This function handles the complexity of GitHub release naming conventions:
    1. Some projects use 'v' prefixes in tags but not in filenames.
    2. Some projects use dashes, others dots.
    3. We support custom 'archive_name' patterns to handle any edge case.
    """
    name = data['name']
    version = data['version']
    repo = data['upstream']['repo']
    binary_name = data['build']['binary_name']
    archive_pattern = data['upstream'].get('archive_name')
    
    # We strip the 'v' prefix for filename construction because Go projects
    # typically tag 'v1.0.0' but release 'project-1.0.0.tar.gz'.
    clean_version = version.lstrip('v') if version.startswith('v') else version

    # Construct the download URL
    if archive_pattern:
        # User provided a specific pattern (e.g. for slurm_exporter using dashes)
        filename = archive_pattern.format(
            name=name, 
            version=version,
            clean_version=clean_version,
            arch=arch,
            rpm_arch='x86_64' if arch == 'amd64' else 'aarch64'
        )
    else:
        # Default standard Prometheus naming convention
        upstream_arch = f"linux-{arch}"
        filename = f"{name}-{clean_version}.{upstream_arch}.tar.gz"
    
    url = f"https://github.com/{repo}/releases/download/{version}/{filename}"
    
    click.echo(f"Downloading {url}...")
    local_tar = os.path.join(output_dir, filename)
    
    # We look for the main binary AND any extra binaries (like promtool)
    binaries_to_find = [binary_name] + data['build'].get('extra_binaries', [])
    found_binaries = []
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_tar, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        click.echo(f"Extracting binaries {binaries_to_find}...")
        
        # We need to track extracted dirs to clean them up later
        extracted_dirs = set()
        
        with tarfile.open(local_tar, "r:gz") as tar:
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
                    tar.extract(member_to_extract, path=output_dir)
                    extracted_path = os.path.join(output_dir, member_to_extract.name)
                    final_path = os.path.join(output_dir, b_name)
                    
                    if extracted_path != final_path:
                        shutil.move(extracted_path, final_path)
                    
                    parts = member_to_extract.name.split('/')
                    if len(parts) > 1:
                        extracted_dirs.add(parts[0])
                    
                    os.chmod(final_path, 0o755)
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
            click.echo("Error: No binaries found in archive.", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"Failed to process artifact: {e}", err=True)
        raise e
    finally:
        if os.path.exists(local_tar):
            os.remove(local_tar)

def download_extra_sources(data, output_dir):
    """
    Download additional files (like config examples) that are not in the release tarball.
    """
    extra_sources = data.get('build', {}).get('extra_sources', [])
    for source in extra_sources:
        url = source['url']
        filename = source['filename']
        click.echo(f"Downloading extra source: {url}...")
        try:
            r = requests.get(url)
            r.raise_for_status()
            with open(os.path.join(output_dir, filename), 'wb') as f:
                f.write(r.content)
            click.echo(f"Extra source saved as {filename}")
        except Exception as e:
            click.echo(f"Warning: Failed to download extra source {url}: {e}")

@click.command()
@click.option('--manifest', '-m', help='Path to manifest', required=True)
@click.option('--output-dir', '-o', help='Output directory', default='./build')
@click.option('--arch', '-a', help='Target arch', default='amd64')
def build(manifest, output_dir, arch):
    click.echo(f"Processing {manifest} ({arch})")
    
    try:
        data = load_manifest(manifest)
        data['arch'] = arch
        rpm_arch_map = {'amd64': 'x86_64', 'arm64': 'aarch64'}
        data['rpm_arch'] = rpm_arch_map.get(arch, arch)
        
        # Setup Jinja2 with Override Logic:
        # We look in the exporter's 'templates' folder first.
        # If not found, we use the global 'core/templates' folder.
        template_dirs = [
            os.path.join(os.path.dirname(manifest), 'templates'),
            os.path.join(os.path.dirname(__file__), 'templates')
        ]
        env = Environment(loader=FileSystemLoader(template_dirs))
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Prepare binaries and assets
        download_and_extract(data, output_dir, arch)
        download_extra_sources(data, output_dir)

        # 2. Build RPM Spec
        artifacts = data.get('artifacts', {})
        if artifacts.get('rpm', {}).get('enabled'):
            # Smart Copy Logic:
            # Files can come from local 'assets/' OR be downloaded extra sources.
            for extra_file in artifacts['rpm'].get('extra_files', []):
                source_path = extra_file['source']
                local_src = os.path.join(os.path.dirname(manifest), source_path)
                downloaded_src = os.path.join(output_dir, source_path)
                
                dst_name = os.path.basename(source_path)
                
                if os.path.exists(local_src):
                    shutil.copy(local_src, os.path.join(output_dir, dst_name))
                elif os.path.exists(downloaded_src):
                    # It's a downloaded source, already there, just ensure name match
                    if downloaded_src != os.path.join(output_dir, dst_name):
                         shutil.copy(downloaded_src, os.path.join(output_dir, dst_name))
                else:
                    click.echo(f"Warning: Source file {source_path} not found.")
                
                extra_file['build_source'] = dst_name

            # Try to load custom template if it exists, else default
            try:
                template = env.get_template(f"{data['name']}.spec.j2")
                click.echo(f"Using custom spec template")
            except:
                template = env.get_template('default.spec.j2')

            output_content = template.render(data)
            output_file = os.path.join(output_dir, f"{data['name']}.spec")
            with open(output_file, 'w') as f:
                f.write(output_content)
            
        # 3. Build Dockerfile
        if artifacts.get('docker', {}).get('enabled'):
            # Same override logic for Dockerfile
            try:
                template = env.get_template('Dockerfile.j2')
            except:
                template = env.get_template('Dockerfile.j2') # Fallback to same name but different path

            output_content = template.render(data)
            output_file = os.path.join(output_dir, "Dockerfile")
            with open(output_file, 'w') as f:
                f.write(output_content)
            
    except Exception as e:
        if not isinstance(e, click.Abort):
            click.echo(f"Error: {e}", err=True)
        raise e

if __name__ == '__main__':
    build()
