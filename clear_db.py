import sqlite3
import os

DATA_DIR = "data"  # Adjust if needed
DB_PATH = os.path.abspath(os.path.join(DATA_DIR, "vulnstatus.db"))
BACKUP_PATH = os.path.abspath(os.path.join(DATA_DIR, "vulnstatus_backup.json"))
PREV_BACKUP_PATH = os.path.abspath(os.path.join(DATA_DIR, "vulnstatus_backup_prev.json"))
NEW_SCAN_JSON = os.path.abspath("new_scan.json")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Clear vuln_status table
c.execute("DELETE FROM vuln_status")
conn.commit()
conn.close()

print("Cleared vulnerability data from the database.")

# Remove backup JSON files and new_scan.json if exist
for file_path in [BACKUP_PATH, PREV_BACKUP_PATH, NEW_SCAN_JSON]:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        else:
            print(f"File not found (skipped): {file_path}")
    except Exception as e:
        print(f"Failed to delete {file_path}: {str(e)}")
