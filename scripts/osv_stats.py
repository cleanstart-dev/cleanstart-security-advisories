import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
REPO_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "advisories"))

cve_pattern = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)

advisory_files = []
for root, dirs, files in os.walk(REPO_PATH):
    for f in files:
        if f.endswith(".json"):
            advisory_files.append(os.path.join(root, f))

print(f"Total OSV advisory files: {len(advisory_files)}")

cve_ids = set()
publish_dates = []

for file in advisory_files:
    with open(file, "r") as fh:
        data = json.load(fh)

    # ✅ 1. Check aliases
    for alias in data.get("aliases", []):
        if cve_pattern.match(alias):
            cve_ids.add(alias.upper())

    # ✅ 2. Check upstream (your case)
    for up in data.get("upstream", []):
        if cve_pattern.match(up):
            cve_ids.add(up.upper())

    # published date
    published = data.get("published")
    if published:
        try:
            publish_dates.append(datetime.fromisoformat(published.replace("Z", "+00:00")))
        except:
            pass

print(f"Unique CVE IDs: {len(cve_ids)}")
print("List of CVEs:", sorted(cve_ids))

if publish_dates:
    earliest = min(publish_dates)
    latest = max(publish_dates)
    print("Earliest advisory published:", earliest.isoformat())
    print("Latest advisory published:", latest.isoformat())
