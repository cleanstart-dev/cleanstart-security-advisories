from flask import Flask, jsonify, request, send_file
from flask import Response, stream_with_context
from flask_cors import CORS
import sqlite3
import json
import os
import sys
import subprocess
import re
import io
import csv
import shutil

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.abspath("data/vulnstatus.db")
BACKUP_PATH = os.path.abspath("data/vulnstatus_backup.json")
PREV_BACKUP_PATH = os.path.abspath("data/vulnstatus_backup_prev.json")
ANALYZER_PATH = os.path.abspath("analyzer/scan_analyze.py")
SCAN_RESULTS_DIR = os.path.abspath("scan_results")
# Change this to your actual gsutil.cmd path:
#GSUTIL_PATH = r"C:\Users\Admin\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gsutil.cmd"

GSUTIL_PATH = shutil.which("gsutil")

if GSUTIL_PATH is None:
    raise FileNotFoundError("gsutil not found in Ubuntu PATH. Install Google Cloud SDK.")

print("Using gsutil:", GSUTIL_PATH)

def fetch_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT folder, image_version, cve, status, notes, library, installed_version, fixed_version, severity, description FROM vuln_status')
    results = c.fetchall()
    conn.close()
    out = {}
    for folder, imgver, cve, status, notes, library, installed_version, fixed_version, severity, description in results:
        out.setdefault(folder, {}).setdefault(imgver, {})[cve] = {
            "status": status,
            "notes": notes,
            "library": library,
            "installed_version": installed_version,
            "fixed_version": fixed_version,
            "severity": severity,
            "description": description,
        }
    return out

def export_backup():
    data = fetch_status()
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_previous_backup():
    if os.path.exists(PREV_BACKUP_PATH):
        with open(PREV_BACKUP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_new_backup():
    if os.path.exists(BACKUP_PATH):
        with open(BACKUP_PATH, "r", encoding="utf-8") as src, open(PREV_BACKUP_PATH, "w", encoding="utf-8") as dst:
            dst.write(src.read())

def is_cve_id(key):
    return re.match(r'^CVE-\d{4}-\d+$', str(key) or '')

def normalize_key(key):
    return key.strip().lower() if key else ""

@app.route("/api/vulns", methods=["GET"])
def get_vulns():
    folder = request.args.get("folder")
    data = fetch_status()
    if folder:
        return jsonify({folder: data.get(folder, {})})
    return jsonify(data)

@app.route("/api/vuln/update", methods=["POST"])
def update_vuln():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'UPDATE vuln_status SET status=?, notes=?, updated=datetime("now") WHERE image_version=? AND cve=?',
        (data['status'], data.get('notes', ''), data['image_version'], data['cve'])
    )
    conn.commit()
    conn.close()
    export_backup()
    return jsonify({"success": True})

@app.route("/api/vulns/previous", methods=["GET"])
def previous_vulns():
    if os.path.exists(PREV_BACKUP_PATH):
        with open(PREV_BACKUP_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.route("/api/export/new_json", methods=["GET"])
def export_new_vuln_json():
    current_data = fetch_status()
    prev_data = get_previous_backup()
    new_vulns = []
    for folder in current_data:
        for image_version in current_data[folder]:
            for cve in current_data[folder][image_version]:
                if folder not in prev_data or image_version not in prev_data.get(folder, {}) or cve not in prev_data.get(folder, {}).get(image_version, {}):
                    vuln = current_data[folder][image_version][cve]
                    entry = {
                        "folder": folder,
                        "image_version": image_version,
                        "cve": cve,
                        **vuln
                    }
                    new_vulns.append(entry)
    json_bytes = json.dumps(new_vulns, indent=2).encode("utf-8")
    return send_file(io.BytesIO(json_bytes), mimetype='application/json',
                     as_attachment=True, download_name='new_vulnerabilities.json')

@app.route("/api/export/new_csv", methods=["GET"])
def export_new_vuln_csv():
    current_data = fetch_status()
    prev_data = get_previous_backup()
    new_vulns = []
    for folder in current_data:
        for image_version in current_data[folder]:
            for cve in current_data[folder][image_version]:
                if folder not in prev_data or image_version not in prev_data.get(folder, {}) or cve not in prev_data.get(folder, {}).get(image_version, {}):
                    vuln = current_data[folder][image_version][cve]
                    vuln_row = {
                        "folder": folder,
                        "image_version": image_version,
                        "cve": cve,
                        "status": vuln.get("status", ""),
                        "notes": vuln.get("notes", ""),
                        "library": vuln.get("library", ""),
                        "installed_version": vuln.get("installed_version", ""),
                        "fixed_version": vuln.get("fixed_version", ""),
                        "severity": vuln.get("severity", ""),
                        "description": vuln.get("description", ""),
                    }
                    new_vulns.append(vuln_row)
    if not new_vulns:
        return jsonify({"error": "No new vulnerabilities to export"}), 404
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=new_vulns[0].keys())
    writer.writeheader()
    writer.writerows(new_vulns)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='new_vulnerabilities.csv')

@app.route("/api/run_scan", methods=["POST"])
def run_scan():
    save_new_backup()
    old_data = get_previous_backup()
    subprocess.run([sys.executable, ANALYZER_PATH], check=True)
    export_backup()
    new_data = fetch_status()
    fixed_count = 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    conn.commit()
    conn.close()
    new_vulns = []
    for folder in new_data:
        for image_version in new_data[folder]:
            for cve in new_data[folder][image_version]:
                if folder not in old_data or image_version not in old_data.get(folder, {}) or cve not in old_data.get(folder, {}).get(image_version, {}):
                    new_vulns.append({
                        "folder": folder,
                        "image_version": image_version,
                        "cve": cve
                    })
    return jsonify({"new_vulns": new_vulns, "count": len(new_vulns)})



@app.route("/api/progress_download_gcp_results", methods=["GET", "POST"])
def progress_download_gcp_results():
    # Accept folder_name from POST JSON body or GET query param
    if request.method == "POST":
        data = request.json
        folder_name = data.get("folder_name", "").strip() if data else ""
    else:
        folder_name = request.args.get("folder_name", "").strip()

    if not folder_name:
        return Response("data: ERROR: folder_name required\n\n", mimetype="text/event-stream")

    # Clear the scan_results directory BEFORE streaming starts
    try:
        for filename in os.listdir(SCAN_RESULTS_DIR):
            filepath = os.path.join(SCAN_RESULTS_DIR, filename)
            if os.path.isfile(filepath) or os.path.islink(filepath):
                os.unlink(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
    except Exception as e:
        return Response(f"data: ERROR: Could not clear scan_results: {str(e)}\n\n", mimetype="text/event-stream")

    def generate():
        gcp_paths = [
            f"gs://clnstrt-vuln-result/{folder_name}/batch-2",
            f"gs://clnstrt-vuln-result/{folder_name}/bouncycastle",
            f"gs://clnstrt-vuln-result/{folder_name}/community",
            f"gs://clnstrt-vuln-result/{folder_name}/non-fips",
            f"gs://clnstrt-vuln-result/{folder_name}/openssl",
        ]

        cmd = [GSUTIL_PATH, "-m", "cp", "-r"] + gcp_paths + [SCAN_RESULTS_DIR]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in proc.stdout:
                yield f"data: {line.rstrip()}\n\n"
            proc.stdout.close()
            proc.wait()
            yield "data: DONE\n\n"
        except Exception as e:
            yield f"data: ERROR: {str(e)}\n\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"  # if using nginx reverse proxy
    }

    return Response(stream_with_context(generate()), headers=headers)

SYNC_SCRIPT = os.path.abspath("sqlite_to_postgres_sync.py")
@app.route("/api/sync_sqlite_to_postgres", methods=["POST"])
def sync_sqlite_to_postgres():
    try:
        # Run the sync script, capture output for feedback
        proc = subprocess.run([sys.executable, SYNC_SCRIPT], capture_output=True, text=True, check=True)
        return jsonify({"status": "success", "msg": proc.stdout})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "msg": e.stderr}), 500
    
import json


here = os.path.dirname(os.path.abspath(__file__))
users_file_path = os.path.join(here, "users.json")

# Load user credentials from JSON file using the absolute path
with open(users_file_path, "r") as f:
    users = json.load(f)


@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    if username in users and users[username] == password:
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


