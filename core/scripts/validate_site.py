#!/usr/bin/env python3
import json
import os
import sys


def check_file(path, min_size=100):
    if not os.path.exists(path):
        print(f"❌ Error: File missing: {path}")
        return False

    size = os.path.getsize(path)
    if size < min_size:
        print(f"❌ Error: File too small ({size} bytes): {path}")
        return False

    print(f"✅ File present: {path} ({size} bytes)")
    return True


def validate_json(path):
    try:
        with open(path) as f:
            data = json.load(f)
            count = len(data.get("exporters", []))
            print(f"✅ JSON valid: {count} exporters found in catalog")
            return True
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading {path}: {e}")
        return False


def validate_html(path):
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()

        checks = [
            ("<title>Monitoring Hub", "Page Title"),
            ('id="exporters-data"', "Exporters Data Script"),
            ('id="categories-data"', "Categories Data Script"),
            ('x-data="registry()"', "Alpine.js Initialization"),
        ]

        failed = False
        for snippet, name in checks:
            if snippet not in content:
                print(f"❌ Error: HTML missing '{name}'")
                failed = True
            else:
                print(f"✅ HTML contains '{name}'")

        return not failed
    except Exception as e:
        print(f"❌ Error reading HTML {path}: {e}")
        return False


def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    index_path = os.path.join(base_dir, "index.html")
    catalog_path = os.path.join(base_dir, "catalog.json")

    print(f"🔍 Validating site in: {base_dir}")

    success = True
    success &= check_file(index_path)
    success &= check_file(catalog_path)

    if success:
        success &= validate_json(catalog_path)
        success &= validate_html(index_path)

    if success:
        print("\n🎉 Site Validation PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Site Validation FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
