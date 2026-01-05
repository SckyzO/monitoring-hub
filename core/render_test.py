import json
import os
from jinja2 import Environment, FileSystemLoader

# Mock Data simulating the final JSON injected by gen_site.py
MOCK_EXPORTERS = [
    {
        "name": "node_exporter",
        "version": "1.8.2",
        "description": "Prometheus exporter for hardware and OS metrics exposed by *NIX kernels.",
        "category": "System",
        "new": False,
        "updated": True,
        "upstream": {"repo": "prometheus/node_exporter"},
        "artifacts": {
            "rpm": {"targets": ["el8", "el9", "el10"]},
            "docker": {"enabled": True, "validation": {"port": 9100}}
        },
        "build": {"archs": ["amd64", "arm64"]},
        "readme": "# Node Exporter\nThis is a *mock* readme content for testing the drawer."
    },
    {
        "name": "mysqld_exporter",
        "version": "0.15.1",
        "description": "Prometheus exporter for MySQL server metrics.",
        "category": "Database",
        "new": True,
        "updated": False,
        "upstream": {"repo": "prometheus/mysqld_exporter"},
        "artifacts": {
            "rpm": {"targets": ["el9"]},
            "docker": {"enabled": True}
        },
        "build": {"archs": ["amd64"]}
    }
]

MOCK_CATEGORIES = ["System", "Database", "Web", "Messaging", "Storage"]

def render():
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('index_v2.html.j2')
    
    # Render with JSON strings as the real generator does
    output = template.render(
        exporters_json=json.dumps(MOCK_EXPORTERS),
        categories_json=json.dumps(MOCK_CATEGORIES)
    )
    
    with open('index_v2.html', 'w') as f:
        f.write(output)
    print("✅ index_v2.html generated successfully.")

if __name__ == "__main__":
    render()
