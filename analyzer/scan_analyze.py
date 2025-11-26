import os
import json
import sqlite3
from datetime import datetime
from config import SEARCH_ROOT, BACKUP_JSON, DB_PATH

def scan_json_files():
    vuln_map = {}
    image_to_folder = {}

    for root, dirs, files in os.walk(SEARCH_ROOT):
        folder = os.path.relpath(root, SEARCH_ROOT)
        if folder == ".":
            continue
        for file in files:
            # Only process .json files that are not sbom.json
            if not file.endswith('.json') or file.endswith('-sbom.json'):
                continue
            filepath = os.path.join(root, file)
            with open(filepath, encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception:
                    continue
                # Robust image_version extraction
                image_version = ""
                if isinstance(data, dict):
                    meta = data.get("metadata", {})
                    imgname = meta.get("image_name") if isinstance(meta, dict) else None
                    root_img = data.get("image_name")
                    if imgname and isinstance(imgname, str) and imgname.strip():
                        image_version = imgname.strip()
                    elif root_img and isinstance(root_img, str) and root_img.strip():
                        image_version = root_img.strip()
                    else:
                        image_version = os.path.splitext(file)[0]
                else:
                    image_version = os.path.splitext(file)[0]
                # Always map folder
                image_to_folder[image_version] = folder
                vulns = data.get('vulnerabilities', [])
                if image_version not in vuln_map:
                    vuln_map[image_version] = {}
                for v in vulns:
                    cve = v.get("id") or v.get("cve") or v.get("CVE")
                    if not cve:
                        continue
                    vuln_map[image_version][cve] = {
                        "cve": cve,
                        "severity": v.get("severity", "Unknown"),
                        "package": v.get("package", v.get("pkgName", "")),
                        "library": v.get("library", v.get("package", v.get("pkgName", ""))),
                        "installed_version": v.get("installed_version", v.get("version", v.get("installedVersion", ""))),
                        "fixed_version": v.get("fixed_version", v.get("fixVersion", v.get("fixedVersion", ""))),
                        "description": v.get("description", ""),
                        "folder": folder,
                        "data": v
                    }
    # Ensure even 'no vuln' images are tracked for NO_CVE
    for img in image_to_folder:
        if img not in vuln_map:
            vuln_map[img] = {}

    return vuln_map, image_to_folder

def load_status_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vuln_status (
        folder TEXT,
        image_version TEXT,
        cve TEXT,
        status TEXT,
        updated TEXT,
        notes TEXT,
        library TEXT,
        installed_version TEXT,
        fixed_version TEXT,
        severity TEXT,
        description TEXT,
        PRIMARY KEY (image_version, cve)
    )''')
    return conn, c

def update_and_sync(vuln_map, image_to_folder, conn, c):
    status_backup = {}
    reappeared_alerts = []
    for image_version, cve_dict in vuln_map.items():
        for cve, v in cve_dict.items():
            folder = v.get("folder") or image_to_folder.get(image_version, "")
            c.execute('SELECT status, notes FROM vuln_status WHERE image_version=? AND cve=?', (image_version, cve))
            result = c.fetchone()
            library = v.get('library') or v.get('package') or v.get('pkgName') or v.get('library_name') or ''
            installed_version = v.get('installed_version') or v.get('version') or v.get('installedVersion') or ''
            fixed_version = v.get('fixed_version') or v.get('fixVersion') or v.get('fixedVersion') or ''
            severity = v.get('severity', '')
            description = v.get('description', '')
            if not result:
                c.execute('''INSERT INTO vuln_status
                    (folder, image_version, cve, status, updated, notes, library,
                     installed_version, fixed_version, severity, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (folder, image_version, cve, "UnderInvestigation", datetime.utcnow().isoformat(),
                     "", library, installed_version, fixed_version, severity, description)
                )
                status, notes = "UnderInvestigation", ""
            else:
                status, notes = result
                if status == "Fixed":
                    status = "UnderInvestigation"
                    reappeared_alerts.append({
                        "image_version": image_version,
                        "cve": cve,
                        "message": f"CVE {cve} reappeared in {image_version} after being marked Fixed!"
                    })
                c.execute('''UPDATE vuln_status SET
                        folder=?, library=?, installed_version=?, fixed_version=?, severity=?, description=?, updated=?, status=?
                    WHERE image_version=? AND cve=?''',
                    (folder, library, installed_version, fixed_version, severity, description,
                        datetime.utcnow().isoformat(), status, image_version, cve)
                )
            if image_version not in status_backup:
                status_backup[image_version] = {}
            status_backup[image_version][cve] = {
                "status": status,
                "notes": notes,
                "severity": severity,
                "description": description,
                "library": library,
                "installed_version": installed_version,
                "fixed_version": fixed_version,
                "folder": folder,
            }
        # Insert NO_CVE for vuln-free images
        if not cve_dict:
            folder = image_to_folder.get(image_version, "")
            c.execute("SELECT 1 FROM vuln_status WHERE image_version=? AND cve=?", (image_version, "NO_CVE"))
            if not c.fetchone():
                c.execute("""INSERT INTO vuln_status
                             (folder, image_version, cve, status, updated, notes, library, installed_version, fixed_version, severity, description)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (folder, image_version, "NO_CVE", "No Vulnerabilities",
                           datetime.utcnow().isoformat(), "No vulnerabilities found for this image", "", "", "", "", ""))
                status_backup.setdefault(image_version, {})["NO_CVE"] = {
                    "status": "No Vulnerabilities",
                    "notes": "No vulnerabilities found for this image",
                    "severity": "",
                    "description": "",
                    "library": "",
                    "installed_version": "",
                    "fixed_version": "",
                    "folder": folder,
                }

    # Mark CVEs as Fixed if missing in new scan
    for image_version in status_backup.keys():
        c.execute('SELECT cve, status FROM vuln_status WHERE image_version=?', (image_version,))
        db_cves = c.fetchall()
        current_cves = set(vuln_map.get(image_version, {}).keys())
        for db_cve, db_status in db_cves:
            if db_cve not in current_cves and db_status != "Fixed":
                c.execute('UPDATE vuln_status SET status=?, updated=? WHERE image_version=? AND cve=?',
                          ("Fixed", datetime.utcnow().isoformat(), image_version, db_cve))
                if image_version in status_backup and db_cve in status_backup[image_version]:
                    status_backup[image_version][db_cve]["status"] = "Fixed"
    conn.commit()
    with open(BACKUP_JSON, "w", encoding="utf-8") as f:
        json.dump(status_backup, f, indent=2)
    return status_backup, reappeared_alerts

if __name__ == "__main__":
    vuln_map, image_to_folder = scan_json_files()
    conn, c = load_status_db()
    status_backup, reappeared_alerts = update_and_sync(vuln_map, image_to_folder, conn, c)
    print("Scan complete. Backup written. Example output:")
    print(json.dumps(status_backup, indent=2))
    if reappeared_alerts:
        print("\n=== ALERT: Reappeared CVEs ===")
        for alert in reappeared_alerts:
            print(alert["message"])
