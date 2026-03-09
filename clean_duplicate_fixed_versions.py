import os
import json
import sys
from datetime import datetime

# Run from repo root or scripts/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
BASE_DIR = os.path.join(REPO_ROOT, "advisories")

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


# (pkg, fixed_ver) -> [(path, published), ...]
entries = {}

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if not file.endswith(".json"):
            continue
        path = os.path.join(root, file)
        try:
            with open(path) as f:
                data = json.load(f)
            published = parse_date(data.get("published", ""))
            for pair in extract_package_fixed_versions(data):
                entries.setdefault(pair, []).append((path, published))
        except Exception as e:
            print(f"Error reading {path}: {e}")

# Har pair ke liye latest file keep, baaki delete list mein (baad mein delete)
# Ek hi file kisi aur pair ke liye "keep" ho sakti hai, isliye pehle keep set banao
to_keep = set()
to_delete = []  # (path, pair) for logging

for pair, file_list in entries.items():
    if len(file_list) <= 1:
        continue
    file_list.sort(key=lambda x: x[1], reverse=True)  # latest first
    keep_path = file_list[0][0]
    to_keep.add(keep_path)
    for path, _ in file_list[1:]:
        to_delete.append((path, pair))

# Sirf wahi delete karo jo kisi bhi pair ke liye "keep" nahi hai; har path sirf ek baar
actually_delete = []
seen_remove = set()
for path, pair in to_delete:
    if path in to_keep or path in seen_remove:
        continue
    seen_remove.add(path)
    actually_delete.append((path, pair))

# Report and delete (har path sirf ek baar)
deleted_files = []
for path, pair in actually_delete:
    print(f"\nDuplicate: {pair[0]} @ {pair[1]}")
    print(f"   Deleting: {path}")
    if not DRY_RUN and os.path.isfile(path):
        os.remove(path)
        deleted_files.append(path)

if DRY_RUN:
    print("\n🟡 Dry run. No files deleted.")
else:
    print(f"\n🧹 Deleted {len(deleted_files)} duplicate file(s).")
