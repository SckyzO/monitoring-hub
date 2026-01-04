import os
import json
import yaml
import requests
import sys

def get_remote_catalog(catalog_url="https://sckyzo.github.io/monitoring-hub/catalog.json"):
    """
    Fetches the current state of the repository from the deployed catalog.json.
    Returns a dictionary keyed by exporter name with version info.
    """
    try:
        print(f"Fetching remote catalog from {catalog_url}...", file=sys.stderr)
        r = requests.get(catalog_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Convert list to dict for easier lookup: {'node_exporter': '1.8.1', ...}
            return {item['name']: item['version'] for item in data.get('exporters', [])}
        else:
            print(f"Warning: Remote catalog not found (Status {r.status_code}). Assuming empty state.", file=sys.stderr)
            return {}
    except Exception as e:
        print(f"Warning: Could not fetch remote catalog: {e}. Assuming empty state.", file=sys.stderr)
        return {}

def get_local_state(exporters_dir="exporters"):
    """
    Reads all local manifest.yaml files to build the current desired state.
    """
    local_state = {}
    if not os.path.isdir(exporters_dir):
        return {}

    for exporter_name in os.listdir(exporters_dir):
        manifest_path = os.path.join(exporters_dir, exporter_name, "manifest.yaml")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    data = yaml.safe_load(f)
                    # Normalize version (strip 'v' prefix if present to match catalog standard)
                    version = data['version'].lstrip('v')
                    local_state[exporter_name] = version
            except Exception as e:
                print(f"Error reading {manifest_path}: {e}", file=sys.stderr)
    return local_state

def main():
    # Allow overriding catalog URL for testing or forks
    catalog_url = os.environ.get('CATALOG_URL', "https://sckyzo.github.io/monitoring-hub/catalog.json")
    force_rebuild = os.environ.get('FORCE_REBUILD', 'false').lower() == 'true'
    # Allow filtering by specific exporter if running manually
    target_exporter = os.environ.get('TARGET_EXPORTER')

    remote_state = get_remote_catalog(catalog_url)
    local_state = get_local_state()

    to_build = []

    print("\n--- Smart Build Analysis ---", file=sys.stderr)
    for name, local_version in local_state.items():
        if target_exporter and name != target_exporter:
            continue

        remote_version = remote_state.get(name)

        if force_rebuild:
             print(f"[BUILD] {name}: Forced rebuild.", file=sys.stderr)
             to_build.append(name)
             continue

        if remote_version is None:
            print(f"[BUILD] {name}: New exporter (Local: {local_version}).", file=sys.stderr)
            to_build.append(name)
        elif str(local_version) != str(remote_version):
            print(f"[BUILD] {name}: Version update ({remote_version} -> {local_version}).", file=sys.stderr)
            to_build.append(name)
        else:
            print(f"[SKIP]  {name}: Up to date ({local_version}).", file=sys.stderr)

    # Output for GitHub Actions
    # We dump ONLY the JSON array to stdout so it can be captured easily
    json_output = json.dumps(to_build)
    
    # Write to GITHUB_OUTPUT if running in Actions
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"exporters={json_output}\n")
    else:
        # If running locally, print just the JSON to stdout for piping
        print(json_output)

if __name__ == "__main__":
    main()
