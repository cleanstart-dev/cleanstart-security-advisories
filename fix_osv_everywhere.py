import json
import subprocess
import re
import sys

DRY_RUN = "--dry-run" in sys.argv

# match ghsa in ANY case
ghsa_regex = re.compile(r"ghsa-[a-z0-9\-]+", re.IGNORECASE)

BASE = "github.com/cleanstart-dev/cleanstart-security-advisories"


def fix_string(s: str):
    original = s

    # ---- normalize GHSA ids ----
    def normalize(m):
        v = m.group(0)
        return "GHSA-" + v[5:].lower()

    s = ghsa_regex.sub(normalize, s)

    # ---- add .json to advisory link ----
    if BASE in s and not s.endswith(".json"):
        s = s + ".json"

    return s, s != original


def walk(v):
    changed = False

    if isinstance(v, str):
        return fix_string(v)

    if isinstance(v, list):
        new_list = []
        for i in v:
            new, c = walk(i)
            changed |= c
            new_list.append(new)
        return new_list, changed

    if isinstance(v, dict):
        new_dict = {}
        for k, val in v.items():
            new, c = walk(val)
            changed |= c
            new_dict[k] = new
        return new_dict, changed

    return v, False


# 🎯 only json files changed in PR
files = (
    subprocess.check_output(["git", "diff", "--name-only", "origin/main"])
    .decode()
    .splitlines()
)

for file in files:
    if not file.endswith(".json"):
        continue

    try:
        with open(file) as f:
            data = json.load(f)
    except Exception:
        continue

    new_data, changed = walk(data)

    if changed:
        print("Updating:", file)
        if not DRY_RUN:
            with open(file, "w") as f:
                json.dump(new_data, f, indent=2)
                f.write("\n")
