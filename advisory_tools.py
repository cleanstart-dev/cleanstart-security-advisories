#!/usr/bin/env python3
"""
advisory_tools.py — All-in-one tool for cleanstart-security-advisories repo.

Usage:
    python advisory_tools.py process-all
    python advisory_tools.py process-all --dry-run
    python advisory_tools.py merge-prs
    python advisory_tools.py final-merge
    python advisory_tools.py check-duplicates
    python advisory_tools.py clean-duplicates [--dry-run]
    python advisory_tools.py normalize [--dry-run]
"""

import os
import json
import sys
import re
import subprocess
import argparse
from datetime import datetime

# ─────────────────────────────────────────────
# GLOBAL CONFIG
# ─────────────────────────────────────────────

REPO          = "cleanstart-dev/cleanstart-security-advisories"
BASE_BRANCH   = "check"

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT     = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "scripts" else SCRIPT_DIR
BASE_DIR      = os.path.join(REPO_ROOT, "advisories")

GHSA_REGEX    = re.compile(r"ghsa-[a-z0-9\-]+", re.IGNORECASE)
ADVISORY_BASE = "github.com/cleanstart-dev/cleanstart-security-advisories"


# ─────────────────────────────────────────────
# HELPER — shell command runner
# ─────────────────────────────────────────────

def run(cmd, check=True):
    print(f"   $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
    return result.returncode, result.stdout.strip()


# ─────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────

def extract_package_fixed_versions(data):
    results = []
    for affected in data.get("affected", []):
        pkg = affected.get("package", {}).get("name")
        for r in affected.get("ranges", []):
            for event in r.get("events", []):
                if "fixed" in event:
                    results.append((pkg, event["fixed"]))
    return results


def parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.min


def fix_string(s: str):
    original = s
    def _normalize(m):
        v = m.group(0)
        return "GHSA-" + v[5:].lower()
    s = GHSA_REGEX.sub(_normalize, s)
    if ADVISORY_BASE in s and not s.endswith(".json"):
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


# ─────────────────────────────────────────────
# CHECKOUT HELPER — gh pr checkout ki jagah
# git fetch + git checkout use karo
# (fixes: git 'remote-https' is not a git command)
# ─────────────────────────────────────────────

def checkout_pr_branch(branch):
    """
    gh pr checkout ki jagah manually fetch + checkout karo.
    Pehle branch fetch karo, phir checkout karo.
    """
    # fetch karo
    rc, _ = run(f"git fetch origin {branch}", check=False)
    if rc != 0:
        return False

    # agar branch locally exist karti hai toh sirf checkout karo
    rc_local, _ = run(f"git checkout {branch}", check=False)
    if rc_local == 0:
        # latest remote se sync karo
        run(f"git reset --hard origin/{branch}", check=False)
        return True

    # nahi hai toh naya local branch banao from remote
    rc_new, _ = run(f"git checkout -b {branch} origin/{branch}", check=False)
    return rc_new == 0


# ─────────────────────────────────────────────
# ★ PROCESS-ALL
# ─────────────────────────────────────────────

def process_all(dry_run=False):

    # ── Step 1: check branch sync + seen set load ──
    print(f"\n📦 '{BASE_BRANCH}' branch sync kar rahe hain...\n")

    run("git fetch origin", check=False)
    run(f"git checkout {BASE_BRANCH}", check=False)

    # FIX: divergent branch issue → reset --hard use karo
    run(f"git reset --hard origin/{BASE_BRANCH}", check=False)

    seen = {}
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path) as f:
                    data = json.load(f)
                for pair in extract_package_fixed_versions(data):
                    seen[pair] = path
            except Exception as e:
                print(f"⚠️  Error reading {path}: {e}")

    print(f"✅ {len(seen)} existing entries mili hain '{BASE_BRANCH}' mein.\n")

    # ── Step 2: Saare open PRs fetch karo ──
    print(f"📥 Open PRs fetch kar rahe hain...\n")

    _, output = run(
        f'gh pr list --repo {REPO} --base {BASE_BRANCH} --limit 500 --json number,headRefName '
        f'--jq \'.[] | "\\(.number)|\\(.headRefName)"\'',
        check=False
    )

    if not output.strip():
        _, output = run(
            f'gh pr list --repo {REPO} --search "is:open review:required" --limit 500 '
            f'--json number,headRefName --jq \'.[] | "\\(.number)|\\(.headRefName)"\'',
            check=False
        )

    if not output.strip():
        print("✅ Koi bhi open PR nahi mila.")
        return

    pr_lines = [l.strip() for l in output.splitlines() if "|" in l.strip()]
    print(f"🔢 Total PRs: {len(pr_lines)}\n")

    merged_prs  = []
    skipped_prs = []

    # ── Step 3: Har PR process karo ──
    for line in pr_lines:
        pr_number, branch = line.split("|", 1)
        pr_number = pr_number.strip()
        branch    = branch.strip()

        print(f"\n{'='*55}")
        print(f"🔎 PR #{pr_number}  |  Branch: {branch}")
        print(f"{'='*55}")

        # 3a. FIX: gh pr checkout ki jagah manual fetch + checkout
        success = checkout_pr_branch(branch)
        if not success:
            print(f"⚠️  Checkout fail — PR #{pr_number} skip")
            skipped_prs.append((pr_number, "checkout failed"))
            # check branch pe wapas jao
            run(f"git checkout {BASE_BRANCH}", check=False)
            run(f"git reset --hard origin/{BASE_BRANCH}", check=False)
            continue

        run("git fetch origin", check=False)

        # 3b. Is PR ki changed JSON files nikalo
        _, changed_output = run(f"git diff --name-only origin/{BASE_BRANCH}", check=False)
        pr_json_files = [
            f.strip() for f in changed_output.splitlines()
            if f.strip().endswith(".json")
        ]

        if not pr_json_files:
            print(f"ℹ️  PR #{pr_number} mein koi JSON file nahi — skip")
            skipped_prs.append((pr_number, "no json files"))
            run(f"git checkout {BASE_BRANCH}", check=False)
            run(f"git reset --hard origin/{BASE_BRANCH}", check=False)
            continue

        # 3c. Duplicate check
        is_duplicate   = False
        duplicate_info = []

        for json_file in pr_json_files:
            if not os.path.isfile(json_file):
                continue
            try:
                with open(json_file) as f:
                    data = json.load(f)
                for pair in extract_package_fixed_versions(data):
                    if pair in seen:
                        is_duplicate = True
                        duplicate_info.append({
                            "file"         : json_file,
                            "package"      : pair[0],
                            "fixed_ver"    : pair[1],
                            "conflict_with": seen[pair]
                        })
            except Exception as e:
                print(f"⚠️  Error reading {json_file}: {e}")

        if is_duplicate:
            print(f"\n❌ PR #{pr_number} DUPLICATE hai!")
            for d in duplicate_info:
                print(f"   Package     : {d['package']}")
                print(f"   Fixed Ver   : {d['fixed_ver']}")
                print(f"   PR File     : {d['file']}")
                print(f"   Already in  : {d['conflict_with']}")

            if not dry_run:
                print(f"   🗑️  PR #{pr_number} close + branch delete kar rahe hain...")
                run(f"gh pr close {pr_number} --repo {REPO} --delete-branch", check=False)
            else:
                print(f"   🟡 Dry run — close nahi kiya")

            skipped_prs.append((pr_number, "duplicate"))
            run(f"git checkout {BASE_BRANCH}", check=False)
            run(f"git reset --hard origin/{BASE_BRANCH}", check=False)
            continue

        # 3d. Merge try karo — conflict check
        print(f"\n🔀 PR #{pr_number} unique hai — merge try kar rahe hain...")
        rc, _ = run(f"git merge origin/{BASE_BRANCH} --no-edit", check=False)

        if rc != 0:
            print(f"\n❌ PR #{pr_number} mein CONFLICT aaya!")
            run("git merge --abort", check=False)

            if not dry_run:
                print(f"   🗑️  PR #{pr_number} close + branch delete kar rahe hain...")
                run(f"gh pr close {pr_number} --repo {REPO} --delete-branch", check=False)
            else:
                print(f"   🟡 Dry run — close nahi kiya")

            skipped_prs.append((pr_number, "merge conflict"))
            run(f"git checkout {BASE_BRANCH}", check=False)
            run(f"git reset --hard origin/{BASE_BRANCH}", check=False)
            continue

        # 3e. Unique + no conflict → push + approve + merge
        if not dry_run:
            run("git push", check=False)
            run(f"gh pr review {pr_number} --approve --repo {REPO}", check=False)
            rc, _ = run(f"gh pr merge {pr_number} --repo {REPO} --merge --admin", check=False)

            if rc == 0:
                print(f"✅ PR #{pr_number} successfully merged!")
                # seen update karo
                for json_file in pr_json_files:
                    if not os.path.isfile(json_file):
                        continue
                    try:
                        with open(json_file) as f:
                            data = json.load(f)
                        for pair in extract_package_fixed_versions(data):
                            seen[pair] = json_file
                    except Exception:
                        pass
                merged_prs.append(pr_number)
            else:
                print(f"⚠️  PR #{pr_number} merge nahi hua")
                skipped_prs.append((pr_number, "merge failed"))
        else:
            print(f"   🟡 Dry run — PR #{pr_number} merge nahi kiya (unique tha)")
            merged_prs.append(pr_number)

        # check branch pe wapas jao aur sync karo
        run(f"git checkout {BASE_BRANCH}", check=False)
        run(f"git reset --hard origin/{BASE_BRANCH}", check=False)

    # ── Step 4: Summary ──
    print(f"\n{'='*55}")
    print(f"📊 SUMMARY")
    print(f"{'='*55}")
    print(f"✅ Merged  ({len(merged_prs)})  : {', '.join(merged_prs) or 'none'}")
    print(f"❌ Skipped ({len(skipped_prs)}) :")
    for pr, reason in skipped_prs:
        print(f"   PR #{pr}  —  {reason}")

    # ── Step 5: Normalize ──
    if merged_prs:
        print(f"\n✏️  Normalize run kar rahe hain '{BASE_BRANCH}' branch pe...\n")

        if not dry_run:
            run(f"git checkout {BASE_BRANCH}", check=False)
            run(f"git reset --hard origin/{BASE_BRANCH}", check=False)

        normalize_count = 0
        for root, _, files in os.walk(BASE_DIR):
            for file in files:
                if not file.endswith(".json"):
                    continue
                path = os.path.join(root, file)
                try:
                    with open(path) as f:
                        data = json.load(f)
                    new_data, changed = walk(data)
                    if changed:
                        print(f"   Updating: {path}")
                        normalize_count += 1
                        if not dry_run:
                            with open(path, "w") as f:
                                json.dump(new_data, f, indent=2)
                                f.write("\n")
                except Exception as e:
                    print(f"⚠️  Error normalizing {path}: {e}")

        if not dry_run and normalize_count > 0:
            run("git add advisories/", check=False)
            run('git commit -m "normalize: fix GHSA IDs and advisory links"', check=False)
            run(f"git push origin {BASE_BRANCH}", check=False)

        print(f"\n✅ Normalize complete — {normalize_count} file(s) updated.")
    else:
        print("\nℹ️  Koi PR merge nahi hua — normalize skip.")

    print(f"\n🎉 process-all complete!")


# ─────────────────────────────────────────────
# 1. MERGE-PRS
# ─────────────────────────────────────────────

def merge_prs():
    print("🚀 Fetching all open PRs requiring review...")
    _, output = run(
        f'gh pr list --repo {REPO} --search "is:open review:required" --json number --jq ".[].number"',
        check=False
    )
    prs = [p.strip() for p in output.splitlines() if p.strip()]
    if not prs:
        print("✅ No PRs found requiring review.")
    else:
        for pr in prs:
            print(f"\n🔎 Processing PR #{pr}")
            run(f"gh pr review {pr} --approve --repo {REPO}")
            run(f"gh pr edit {pr} --repo {REPO} --base {BASE_BRANCH}")

    print(f"\n🚀 Merging all PRs with base '{BASE_BRANCH}'...")
    _, output = run(
        f'gh pr list --repo {REPO} --base {BASE_BRANCH} --json number --jq ".[].number"',
        check=False
    )
    for pr in [p.strip() for p in output.splitlines() if p.strip()]:
        print(f"\n🔀 Merging PR #{pr}")
        run(f"gh pr merge {pr} --repo {REPO} --merge --admin")
    print("\n🎉 All done!")


# ─────────────────────────────────────────────
# 2. FINAL-MERGE
# ─────────────────────────────────────────────

def final_merge():
    print("📥 Fetching PR list...")
    _, output = run(
        f'gh pr list --repo {REPO} --base {BASE_BRANCH} --json number,headRefName '
        f'--jq \'.[] | "\\(.number)|\\(.headRefName)"\'',
        check=False
    )
    if not output:
        print("✅ No PRs found.")
        return
    for line in output.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        pr_number, branch = line.split("|", 1)
        print(f"\n-------------------------------------")
        print(f"🔎 PR #{pr_number}  |  Branch: {branch}")

        success = checkout_pr_branch(branch.strip())
        if not success:
            print(f"⚠️  Checkout fail — skipping PR #{pr_number}")
            continue

        run("git fetch origin")
        rc, _ = run(f"git merge origin/{BASE_BRANCH} --no-edit", check=False)
        if rc != 0:
            print(f"❌ Conflict — skipping PR #{pr_number}")
            run("git merge --abort", check=False)
            run(f"git checkout {BASE_BRANCH}", check=False)
            continue

        run("git push")
        run(f"gh pr merge {pr_number} --repo {REPO} --merge --admin")
        run(f"git checkout {BASE_BRANCH}", check=False)
        run(f"git reset --hard origin/{BASE_BRANCH}", check=False)

    print("\n🎉 All Done!")


# ─────────────────────────────────────────────
# 3. CHECK-DUPLICATES
# ─────────────────────────────────────────────

def check_duplicates():
    seen, duplicates = {}, []
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if not file.endswith(".json"):
                continue
            path = os.path.join(root, file)
            try:
                with open(path) as f:
                    data = json.load(f)
                for pair in extract_package_fixed_versions(data):
                    if pair in seen:
                        duplicates.append((pair, seen[pair], path))
                    else:
                        seen[pair] = path
            except Exception as e:
                print(f"Error reading {path}: {e}")
    if duplicates:
        print("\n❌ Duplicate package + fixed version found:\n")
        for pair, first_file, second_file in duplicates:
            print(f"Package: {pair[0]}  |  Fixed: {pair[1]}")
            print(f"  First: {first_file}")
            print(f"  Dupe : {second_file}")
            print("-" * 60)
        sys.exit(1)
    else:
        print("✅ All package + fixed version combinations are unique.")


# ─────────────────────────────────────────────
# 4. CLEAN-DUPLICATES
# ─────────────────────────────────────────────

def clean_duplicates(dry_run=False):
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

    to_keep, to_delete = set(), []
    for pair, file_list in entries.items():
        if len(file_list) <= 1:
            continue
        file_list.sort(key=lambda x: x[1], reverse=True)
        to_keep.add(file_list[0][0])
        for path, _ in file_list[1:]:
            to_delete.append((path, pair))

    seen_remove, actually_delete = set(), []
    for path, pair in to_delete:
        if path in to_keep or path in seen_remove:
            continue
        seen_remove.add(path)
        actually_delete.append((path, pair))

    deleted = []
    for path, pair in actually_delete:
        print(f"\nDuplicate: {pair[0]} @ {pair[1]}\n   Deleting: {path}")
        if not dry_run and os.path.isfile(path):
            os.remove(path)
            deleted.append(path)

    print(f"\n🟡 Dry run — no files deleted." if dry_run else f"\n🧹 Deleted {len(deleted)} file(s).")


# ─────────────────────────────────────────────
# 5. NORMALIZE
# ─────────────────────────────────────────────

def normalize(dry_run=False):
    rc, output = run("git diff --name-only origin/main", check=False)
    for file in output.splitlines():
        if not file.endswith(".json"):
            continue
        try:
            with open(file) as f:
                data = json.load(f)
        except Exception:
            continue
        new_data, changed = walk(data)
        if changed:
            print(f"Updating: {file}")
            if not dry_run:
                with open(file, "w") as f:
                    json.dump(new_data, f, indent=2)
                    f.write("\n")
    if dry_run:
        print("🟡 Dry run — no files updated.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Advisory Tools — merged CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    p_all = subparsers.add_parser(
        "process-all",
        help="★ Smart: har PR check → duplicate/conflict → close, unique → merge, phir normalize"
    )
    p_all.add_argument("--dry-run", action="store_true", help="Preview only — kuch delete/merge nahi hoga")

    subparsers.add_parser("merge-prs",       help="Approve + change base + merge all review-required PRs")
    subparsers.add_parser("final-merge",      help="Checkout each PR, merge base, push, then merge PR")
    subparsers.add_parser("check-duplicates", help="Scan advisories/ and fail on duplicate pkg+fixed_version")

    p_clean = subparsers.add_parser("clean-duplicates", help="Delete older duplicate advisory files")
    p_clean.add_argument("--dry-run", action="store_true")

    p_norm = subparsers.add_parser("normalize", help="Fix GHSA IDs + add .json to advisory links")
    p_norm.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "process-all":
        process_all(dry_run=args.dry_run)
    elif args.command == "merge-prs":
        merge_prs()
    elif args.command == "final-merge":
        final_merge()
    elif args.command == "check-duplicates":
        check_duplicates()
    elif args.command == "clean-duplicates":
        clean_duplicates(dry_run=args.dry_run)
    elif args.command == "normalize":
        normalize(dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()