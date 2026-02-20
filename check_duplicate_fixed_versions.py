import os
import json
import sys

BASE_DIR = "./advisories"  # repo root se relative path

seen = {}
duplicates = []

def extract_package_fixed_versions(data):
    results = []

    for affected in data.get("affected", []):
        pkg = affected.get("package", {}).get("name")

        for r in affected.get("ranges", []):
            for event in r.get("events", []):
                if "fixed" in event:
                    fixed_version = event["fixed"]
                    results.append((pkg, fixed_version))

    return results


for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".json"):
            path = os.path.join(root, file)

            try:
                with open(path) as f:
                    data = json.load(f)

                pairs = extract_package_fixed_versions(data)

                for pair in pairs:
                    if pair in seen:
                        duplicates.append((pair, seen[pair], path))
                    else:
                        seen[pair] = path

            except Exception as e:
                print(f"Error reading {path}: {e}")

# Report
if duplicates:
    print("\n❌ Duplicate package + fixed version found:\n")
    for pair, first_file, second_file in duplicates:
        print(f"Package: {pair[0]}")
        print(f"Fixed Version: {pair[1]}")
        print(f"First found in:  {first_file}")
        print(f"Duplicate in:    {second_file}")
        print("-" * 60)
    sys.exit(1)  # CI fail
else:
    print("✅ All package + fixed version combinations are unique.")
