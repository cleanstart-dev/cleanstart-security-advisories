import os
 
# Dynamic path: one folder above analyzer → scan_results
BASE_DIR_CONFIG = os.path.dirname(os.path.abspath(__file__))   # .../Alert/analyzer
SEARCH_ROOT = os.path.join(os.path.dirname(BASE_DIR_CONFIG), "scan_results")
 
# Leave everything else unchanged
BASE_DIR = os.path.abspath(os.path.dirname(__file__) + '/../data')
 
STATUS_CHOICES = ["UnderInvestigation", "Maintainer Issue", "Upstream Fix", "Compatibility Issue"]
 
BACKUP_JSON = os.path.join(BASE_DIR, 'vulnstatus_backup.json')
DB_PATH = os.path.join(BASE_DIR, 'vulnstatus.db')