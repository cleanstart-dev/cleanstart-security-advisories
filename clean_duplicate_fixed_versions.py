import os
import json
import sys
from datetime import datetime

BASE_DIR = "./advisories"

DRY_RUN = "--dry-run" in sys.argv

def parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.min

def extract_package_fixed_versions(data):
    results = []
    for affected in data.get("affected", []):
        pkg = affected.get("package", {}).get("name")
        for r in affected.get("ranges", []):
            for event in r.get("events", []):
                if "fixed" in event:
                    results.append((pkg, event["fixed"]))
    return results

# Collect all entries
entries = {}

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".json"):
            path = os.path.join(root, file)
            try:
                with open(path) as f:
                    data = json.load(f)

                published = parse_date(data.get("published", ""))
                pairs = extract_package_fixed_versions(data)

                for pair in pairs:
                    entries.setdefault(pair, []).append((path, published))

            except Exception as e:
                print(f"Error reading {path}: {e}")

deleted_files = []

for pair, file_list in entries.items():
    if len(file_list) > 1:
        # Sort by published date descending (latest first)
        file_list.sort(key=lambda x: x[1], reverse=True)

        keep = file_list[0]
        remove = file_list[1:]

        print("\nDuplicate found:")
        print(f"Package: {pair[0]}")
        print(f"Fixed Version: {pair[1]}")
        print(f"Keeping: {keep[0]}")

        for r in remove:
            print(f"Deleting: {r[0]}")
            if not DRY_RUN:
                os.remove(r[0])
                deleted_files.append(r[0])

if DRY_RUN:
    print("\n🟡 Dry run complete. No files deleted.")
else:
    print(f"\n🧹 Cleanup complete. Deleted {len(deleted_files)} files.")
