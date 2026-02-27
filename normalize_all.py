#!/usr/bin/env python3
"""
normalize_all.py — Saari advisory JSON files normalize karo

Kya fix karta hai:
  1. GHSA IDs → proper format  (ghsa-abc-123 → GHSA-abc-123)
  2. Advisory links mein .json missing hai toh add karo

Usage:
    python normalize_all.py            # sab fix karo
    python normalize_all.py --dry-run  # sirf dekho, kuch change mat karo
"""

import os
import json
import re
import sys

# ── Config ──────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
BASE_DIR      = os.path.join(SCRIPT_DIR, "advisories")
GHSA_REGEX    = re.compile(r"ghsa-[a-z0-9\-]+", re.IGNORECASE)
ADVISORY_BASE = "github.com/cleanstart-dev/cleanstart-security-advisories"
DRY_RUN       = "--dry-run" in sys.argv
# ────────────────────────────────────────────────


def fix_string(s: str):
    original = s

    # Fix 1: GHSA-xxxx-xxxx → uppercase GHSA-, lowercase rest
    def _fix_ghsa(m):
        v = m.group(0)
        return "GHSA-" + v[5:].lower()
    s = GHSA_REGEX.sub(_fix_ghsa, s)

    # Fix 2: advisory link mein .json missing hai toh add karo
    if ADVISORY_BASE in s and not s.endswith(".json"):
        s = s + ".json"

    return s, s != original


def walk(v):
    """Recursively JSON traverse karo aur strings fix karo."""
    changed = False
    if isinstance(v, str):
        return fix_string(v)
    if isinstance(v, list):
        new_list = []
        for item in v:
            new, c = walk(item)
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


def main():
    if not os.path.isdir(BASE_DIR):
        print(f"❌ 'advisories/' folder nahi mila: {BASE_DIR}")
        sys.exit(1)

    # Saari JSON files dhundo
    all_files = []
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith(".json"):
                all_files.append(os.path.join(root, file))

    print(f"📂 Total JSON files mili: {len(all_files)}")
    if DRY_RUN:
        print("🟡 DRY RUN mode — koi file save nahi hogi\n")
    else:
        print()

    updated = []
    errors  = []

    for path in all_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            new_data, changed = walk(data)

            if changed:
                updated.append(path)
                print(f"✏️  Fixing: {path}")
                if not DRY_RUN:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(new_data, f, indent=2, ensure_ascii=False)
                        f.write("\n")

        except Exception as e:
            errors.append((path, str(e)))
            print(f"⚠️  Error: {path} — {e}")

    # Summary
    print(f"\n{'='*50}")
    print(f"📊 SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Fixed files  : {len(updated)}")
    print(f"⏭️  Already OK  : {len(all_files) - len(updated) - len(errors)}")
    print(f"❌ Errors       : {len(errors)}")
    if DRY_RUN:
        print(f"\n🟡 Dry run — koi bhi file save nahi hui")
    else:
        print(f"\n🎉 Normalize complete!")


if __name__ == "__main__":
    main()