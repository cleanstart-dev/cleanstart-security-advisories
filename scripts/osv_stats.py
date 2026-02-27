import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
REPO_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "advisories"))

cve_pattern = re.compile(r"CVE-\d{4}-\d+", re.IGNORECASE)
ghsa_pattern = re.compile(r"GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}", re.IGNORECASE)

advisory_files = []
for root, dirs, files in os.walk(REPO_PATH):
    for f in files:
        if f.endswith(".json"):
            advisory_files.append(os.path.join(root, f))

lines = []
def out(s):
    lines.append(s)
    print(s)

out(f"Total OSV advisory files: {len(advisory_files)}")

cve_ids = set()
ghsa_ids = set()
publish_dates = []

for file in advisory_files:
    with open(file, "r") as fh:
        data = json.load(fh)

    # aliases
    for alias in data.get("aliases", []):
        if cve_pattern.match(alias):
            cve_ids.add(alias.upper())
        if ghsa_pattern.match(alias):
            ghsa_ids.add(alias.upper())

    # upstream
    for up in data.get("upstream", []):
        if cve_pattern.match(up):
            cve_ids.add(up.upper())
        if ghsa_pattern.match(up):
            ghsa_ids.add(up.upper())

    # published date
    published = data.get("published")
    if published:
        try:
            publish_dates.append(datetime.fromisoformat(published.replace("Z", "+00:00")))
        except Exception:
            pass

out(f"Unique CVE IDs: {len(cve_ids)}")
out("List of CVEs: " + str(sorted(cve_ids)))
out(f"Unique GHSA IDs: {len(ghsa_ids)}")
out("List of GHSAs: " + str(sorted(ghsa_ids)))

if publish_dates:
    earliest = min(publish_dates)
    latest = max(publish_dates)
    out("Earliest advisory published: " + earliest.isoformat())
    out("Latest advisory published: " + latest.isoformat())
else:
    out("Earliest advisory published: (none)")
    out("Latest advisory published: (none)")

# Write current data for reference (repo root, else next to script)
for base in [os.path.abspath(os.path.join(BASE_DIR, "..")), BASE_DIR]:
    stats_file = os.path.join(base, "osv_stats.txt")
    try:
        with open(stats_file, "w") as f:
            f.write("\n".join(lines))
        break
    except OSError:
        continue
