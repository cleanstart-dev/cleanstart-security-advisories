#!/usr/bin/env python3
"""
Generate OSV advisories directly from entries in vulnstatus.db.
Creates one advisory per CVE to ensure each JSON maps to a single vulnerability.
"""

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from generate_vulnerability import (
    ADVISORIES_DIR,
    SQLITE_DB_PATH,
    generate_random_vulnerability_id,
    save_vulnerability,
)


def fetch_rows(package_name):
    """Return all DB rows for the given package/library."""
    if not SQLITE_DB_PATH.exists():
        raise FileNotFoundError(f"SQLite DB not found at {SQLITE_DB_PATH}")

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT folder, image_version, cve, status, notes, library,
               installed_version, fixed_version, severity, description, updated
        FROM vuln_status
        WHERE UPPER(library) = UPPER(?)
          AND cve IS NOT NULL
          AND cve != ''
          AND cve != 'NO_CVE'
        ORDER BY cve
        """,
        (package_name,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def build_summary(description, package):
    """Create a concise summary from the description."""
    if description:
        lines = [line.strip() for line in description.splitlines() if line.strip()]
        for line in lines:
            if line.startswith("#"):
                continue
            sentence = line.split(".")[0].strip()
            if sentence:
                return (sentence[:147] + "...") if len(sentence) > 150 else sentence
    return f"Security vulnerability in {package}"


def build_details(row):
    """Construct the advisory details text."""
    description = row[9] or ""
    notes = row[4] or ""
    folder = row[0] or "unknown-folder"
    image_version = row[1] or "unknown-image"

    lines = []
    desc = description.strip()
    if desc:
        lines.append(desc)
    else:
        lines.append("No detailed description was provided by the scanner.")

    lines.append("")
    lines.append(f"Scan source folder: `{folder}`, artifact: `{image_version}`.")
    if notes:
        lines.append("")
        lines.append("Additional notes:")
        lines.append(notes.strip())

    return "\n".join(lines).strip()


def build_affected_entry(package, installed_version, fixed_version):
    """Return an OSV affected entry with ranges/versions."""
    events = [{"introduced": "0"}]
    if fixed_version:
        events.append({"fixed": fixed_version})

    entry = {
        "package": {"ecosystem": "CLEANSTART", "name": package},
        "ranges": [{"type": "ECOSYSTEM", "events": events}],
    }
    versions = []
    if installed_version:
        versions.append(installed_version.strip())
    if versions:
        entry["versions"] = versions
    return entry


def build_references(cve):
    """Return default references for a CVE."""
    return [
        {
            "type": "WEB",
            "url": f"https://nvd.nist.gov/vuln/detail/{cve}",
        }
    ]


def build_severity(severity_label):
    """Return OSV severity block if label exists."""
    label = (severity_label or "").strip().upper()
    if not label or label == "UNKNOWN":
        return []
    return [{"type": "CUSTOM", "score": label}]


def create_advisory(row, package, year, year_dir):
    """Build and save an OSV advisory dict for a single row."""
    folder, image_version, cve, status, notes, _, installed_version, fixed_version, severity, description, updated = row
    vuln_id = generate_random_vulnerability_id(year, year_dir)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    summary = build_summary(description, package)
    details = build_details(row)
    affected = [build_affected_entry(package, installed_version, fixed_version)]
    severity_block = build_severity(severity)
    references = build_references(cve)

    advisory = {
        "schema_version": "1.7.3",
        "id": vuln_id,
        "modified": timestamp,
        "published": timestamp,
        "withdrawn": None,
        "aliases": [cve],
        "summary": summary,
        "details": details,
        "affected": affected,
        "references": references,
        "severity": severity_block,
        "database_specific": {
            "source_folder": folder,
            "image_version": image_version,
            "status": status,
            "notes": notes,
            "generated_from": "db_generate_advisories",
        },
    }

    return advisory


def main():
    parser = argparse.ArgumentParser(
        description="Generate OSV advisories per CVE from vulnstatus.db"
    )
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.utcnow().year,
        help="Year directory for advisories",
    )
    parser.add_argument(
        "--package",
        action="append",
        required=True,
        help="Package/library name as stored in the database (can repeat)",
    )
    args = parser.parse_args()

    year_dir = ADVISORIES_DIR / str(args.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for package in args.package:
        rows = fetch_rows(package)
        if not rows:
            print(f"⚠️  No records found for {package}")
            continue

        print(f"\n=== Generating advisories for {package} ({len(rows)} CVEs) ===")
        for row in rows:
            advisory = create_advisory(row, package, args.year, year_dir)
            filepath = save_vulnerability(advisory, year_dir)
            total += 1
            print(f"  ✓ {filepath.name} (alias: {advisory['aliases'][0]})")

    print(f"\nDone. Created {total} advisories in {year_dir}")


if __name__ == "__main__":
    main()

