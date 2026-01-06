import json
import os
import click
import http.server
import socketserver
from jinja2 import Environment, FileSystemLoader

# Mock Data simulating the final JSON injected by gen_site.py
MOCK_EXPORTERS = [
    {
        "name": "node_exporter",
        "version": "1.8.2",
        "description": "Standard exporter with both RPM and Docker.",
        "category": "System",
        "new": False,
        "updated": True,
        "rpm_status": "success",
        "docker_status": "success",
        "upstream": {"repo": "prometheus/node_exporter"},
        "artifacts": {
            "rpm": {"enabled": True, "targets": ["el8", "el9", "el10"]},
            "docker": {"enabled": True, "validation": {"port": 9100}}
        },
        "build": {"archs": ["amd64", "arm64"]},
        "readme": "# Node Exporter\nStandard case.",
        "availability": {
            "el8": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
            "el9": {"x86_64": {"status": "success"}, "aarch64": {"status": "success"}},
            "el10": {"x86_64": {"status": "success"}, "aarch64": {"status": "na"}}
        }
    },
    {
        "name": "pure_docker_exporter",
        "version": "1.0.0",
        "description": "Exporter with NO RPM support (Docker only). Tab should default to Docker.",
        "category": "Web",
        "new": True,
        "updated": False,
        "rpm_status": "na",
        "docker_status": "success",
        "upstream": {"repo": "test/docker_only"},
        "artifacts": {
            "rpm": {"enabled": False}, # RPM DISABLED
            "docker": {"enabled": True}
        },
        "build": {"archs": ["amd64"]},
        "readme": "# Docker Only\nThis exporter has no RPMs.",
        "availability": {}
    }
]

MOCK_CATEGORIES = ["System", "Web", "Database", "Network", "Storage", "Messaging", "Infrastructure"]

@click.command()
@click.option('--start-webserver', is_flag=True, help='Start a local webserver to preview the site.')
def render(start_webserver):
    """
    Generate a mock portal for UI testing.
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index.html.j2')
    
    # Render with JSON strings as the real generator does
    output = template.render(
        exporters=MOCK_EXPORTERS,
        exporters_json=json.dumps(MOCK_EXPORTERS),
        categories_json=json.dumps(MOCK_CATEGORIES),
        core_version="v0.0.0-test",
        portal_version="v0.0.0-test"
    )
    
    with open('index.html', 'w') as f:
        f.write(output)
    print("✅ index.html generated successfully.")

    if start_webserver:
        PORT = 8000
        Handler = http.server.SimpleHTTPRequestHandler
        # socketserver.TCPServer.allow_reuse_address = True
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"🚀 Preview server started at http://localhost:{PORT}")
                print("💡 Hint: Open your browser and navigate to the URL above.")
                print("Press Ctrl+C to stop the server.")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
        except Exception as e:
            print(f"❌ Could not start server: {e}")

if __name__ == "__main__":
    render()