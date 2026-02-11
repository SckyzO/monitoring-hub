#!/usr/bin/env python3
"""
Aggregate Trivy SARIF results into security statistics.

This script processes Trivy SARIF reports and generates aggregated
security metrics for display in the web portal.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, cast


def parse_sarif_file(sarif_path: Path) -> Dict[str, Any]:
    """Parse a SARIF file and extract vulnerability data."""
    try:
        with open(sarif_path) as f:
            sarif_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Failed to parse {sarif_path}: {e}", file=sys.stderr)
        return {}

    vulnerabilities = []

    # SARIF structure: runs[0].results[]
    for run in sarif_data.get("runs", []):
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown")
            level = result.get("level", "note")  # error, warning, note
            message = result.get("message", {}).get("text", "")

            # Map SARIF level to severity
            severity_map = {
                "error": "CRITICAL",
                "warning": "HIGH",
                "note": "MEDIUM",
                "none": "LOW",
            }
            severity = severity_map.get(level, "UNKNOWN")

            # Extract CVE ID from rule_id or message
            cve_id = rule_id
            if "CVE-" in message:
                # Try to extract CVE from message
                import re

                match = re.search(r"CVE-\d{4}-\d+", message)
                if match:
                    cve_id = match.group(0)

            vulnerabilities.append(
                {
                    "id": cve_id,
                    "severity": severity,
                    "message": message,
                }
            )

    return {
        "vulnerabilities": vulnerabilities,
        "total": len(vulnerabilities),
    }


def aggregate_stats(sarif_dir: Path) -> Dict[str, Any]:
    """Aggregate statistics from all SARIF files."""
    all_vulns: List[Dict[str, Any]] = []
    by_exporter: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_severity: Dict[str, int] = defaultdict(int)

    # Find all SARIF files
    sarif_files = list(sarif_dir.glob("**/*.sarif"))

    if not sarif_files:
        print(f"Warning: No SARIF files found in {sarif_dir}", file=sys.stderr)
        return generate_empty_stats()

    for sarif_file in sarif_files:
        # Extract exporter name from filename (e.g., trivy-node_exporter.sarif)
        exporter_name = sarif_file.stem.replace("trivy-", "").replace("-results", "")

        result = parse_sarif_file(sarif_file)
        vulnerabilities = result.get("vulnerabilities", [])

        # Aggregate
        all_vulns.extend(vulnerabilities)
        by_exporter[exporter_name].extend(vulnerabilities)

        for vuln in vulnerabilities:
            severity = vuln.get("severity", "UNKNOWN")
            by_severity[severity] += 1

    # Sort exporters by vulnerability count
    exporter_counts = [
        {"name": name, "count": len(vulns)} for name, vulns in by_exporter.items()
    ]
    top_exporters = sorted(
        exporter_counts,
        key=lambda x: cast(int, x["count"]),
        reverse=True,
    )[:10]

    return {
        "total_vulnerabilities": len(all_vulns),
        "by_severity": {
            "CRITICAL": by_severity.get("CRITICAL", 0),
            "HIGH": by_severity.get("HIGH", 0),
            "MEDIUM": by_severity.get("MEDIUM", 0),
            "LOW": by_severity.get("LOW", 0),
        },
        "by_exporter": by_exporter,
        "top_exporters": top_exporters,
        "scan_date": datetime.utcnow().isoformat() + "Z",
        "total_exporters_scanned": len(by_exporter),
    }


def generate_empty_stats() -> Dict[str, Any]:
    """Generate empty stats when no SARIF files found."""
    return {
        "total_vulnerabilities": 0,
        "by_severity": {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
        },
        "by_exporter": {},
        "top_exporters": [],
        "scan_date": datetime.utcnow().isoformat() + "Z",
        "total_exporters_scanned": 0,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate Trivy SARIF results into security statistics"
    )
    parser.add_argument(
        "--sarif-dir",
        type=Path,
        default=Path("trivy-results"),
        help="Directory containing SARIF files (default: trivy-results/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("security-stats.json"),
        help="Output JSON file (default: security-stats.json)",
    )

    args = parser.parse_args()

    # Aggregate statistics
    stats = aggregate_stats(args.sarif_dir)

    # Write output
    with open(args.output, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Security statistics written to {args.output}")
    print(f"Total vulnerabilities: {stats['total_vulnerabilities']}")
    print(
        f"  CRITICAL: {stats['by_severity']['CRITICAL']}, "
        f"HIGH: {stats['by_severity']['HIGH']}, "
        f"MEDIUM: {stats['by_severity']['MEDIUM']}, "
        f"LOW: {stats['by_severity']['LOW']}"
    )


if __name__ == "__main__":
    main()
