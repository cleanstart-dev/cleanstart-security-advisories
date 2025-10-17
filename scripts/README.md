# CleanStart Vulnerability Generation Script

This directory contains a unified script to generate vulnerability JSON files in OSV format with comprehensive fields.

## Script

### `generate_vulnerability.py`
Unified script that handles single and batch vulnerability file creation with full OSV schema support.

**Usage:**
```bash
python scripts/generate_vulnerability.py
```

**Features:**
- Three modes: Detailed single, Simple single, and Batch creation
- Auto-generates random unique IDs with format: **LLNNNNN** (2 letters + 5 digits)
- Comprehensive OSV schema support (all fields)
- Interactive prompts for all vulnerability details
- Automatically creates year directories
- Random ID generation with duplicate prevention

---

## Modes

### Mode 1: Detailed Single Vulnerability Creation

Creates one comprehensive vulnerability file with ALL OSV fields including:
- Summary and detailed description
- CVE aliases and upstream references
- Version ranges (introduced/fixed)
- Explicit affected versions list
- Multiple references (ADVISORY, WEB, PACKAGE)
- CVSS severity scores
- Published/modified timestamps

**Example Session:**
```
CleanStart Vulnerability Generator
============================================================

Select mode:
  1. Create single vulnerability (detailed with all fields)
  2. Create single vulnerability (simple - minimal fields)
  3. Create multiple vulnerabilities (batch - simple format)
  4. Exit

Enter choice (1/2/3/4): 1

============================================================
Detailed Vulnerability Creation
============================================================

Enter year (default: 2025): 2025
Generated ID: CLEANSTART-2025-AB12345
Use this ID? (Y/n): Y

Package name (required): python3

Summary (brief one-line description): ZIP64 EOCD validation bypass in Python zipfile module

Details (detailed description, press '.' when done):
The Python 'zipfile' module does not properly validate the ZIP64 EOCD...
.

Aliases (comma-separated, e.g., CVE-2025-1234):
> CVE-2025-8291, BIT-python-2025-8291, PSF-2025-12

Upstream references (comma-separated):
> CVE-2025-8291

CVSS v3 score [optional]: CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N

------------------------------------------------------------
Version Ranges (leave blank to skip)
------------------------------------------------------------
Add version ranges? (y/N): y
  Introduced version: 3.9.0
  Fixed version: 3.9.21
  Add another range? (y/N): y
  Introduced version: 3.10.0
  Fixed version: 3.10.16
  Add another range? (y/N): n

Explicit affected versions (comma-separated) [optional]:
> 3.9.0, 3.9.1, 3.9.20, 3.10.0, 3.10.15

------------------------------------------------------------
References (URLs)
------------------------------------------------------------
Add references? (y/N): y
  URL: https://security.cleanstart.com/advisories/CLEANSTART-2025-PY00001
  Type (ADVISORY/WEB/PACKAGE) [WEB]: ADVISORY
  Add another reference? (y/N): y
  URL: https://nvd.nist.gov/vuln/detail/CVE-2025-8291
  Type (ADVISORY/WEB/PACKAGE) [WEB]: WEB
  Add another reference? (y/N): n

[Preview shows full JSON...]

Create this file? (Y/n): Y

✓ Successfully created: CLEANSTART-2025-AB12345.json
```

---

### Mode 2: Simple Single Vulnerability Creation

Creates one vulnerability file with minimal required fields only:
- ID, modified timestamp
- Package ecosystem and name

Perfect for quick placeholder creation or templates.

**Example Session:**
```
Select mode:
  1. Create single vulnerability (detailed with all fields)
  2. Create single vulnerability (simple - minimal fields)
  3. Create multiple vulnerabilities (batch - simple format)
  4. Exit

Enter choice (1/2/3/4): 2

============================================================
Simple Vulnerability Creation (Minimal Fields)
============================================================

Enter year (default: 2025): 2025
Generated ID: CLEANSTART-2025-XY98765
Use this ID? (Y/n): Y

Package name (or leave blank for placeholder): nginx

============================================================
Preview of JSON to be created:
============================================================
{
  "schema_version": "1.7.3",
  "id": "CLEANSTART-2025-XY98765",
  "modified": "2025-01-15T10:30:00Z",
  "affected": [
    {
      "package": {
        "ecosystem": "CLEANSTART",
        "name": "nginx"
      }
    }
  ]
}

Create this file? (Y/n): Y

✓ Successfully created: CLEANSTART-2025-XY98765.json
```

---

### Mode 3: Batch Vulnerability Creation

Creates multiple simple vulnerability files in one go (minimal fields).

**Example Session:**
```
Select mode:
  1. Create single vulnerability (detailed with all fields)
  2. Create single vulnerability (simple - minimal fields)
  3. Create multiple vulnerabilities (batch - simple format)
  4. Exit

Enter choice (1/2/3/4): 3

============================================================
Batch Vulnerability Creation (Simple Format)
============================================================

Enter year (default: 2025): 2025

How many vulnerability files to create? (default: 5): 3

Enter package names (comma-separated, or leave blank for placeholders):
Package names: nginx, openssl, python3
  Using packages: nginx, openssl, python3

IDs will be generated randomly (format: LLNNNNN)

============================================================
About to create 3 vulnerability files for year 2025
============================================================
Proceed? (Y/n): Y

Generating 3 vulnerability files...
------------------------------------------------------------
✓ Created: CLEANSTART-2025-AB12345.json (package: nginx)
✓ Created: CLEANSTART-2025-CD67890.json (package: openssl)
✓ Created: CLEANSTART-2025-EF24680.json (package: python3)
------------------------------------------------------------

✓ Successfully created 3 files in:
  /path/to/vulnerabilities/2025
```

---

## File Naming Convention

All generated files follow the format:
```
CLEANSTART-YYYY-LLNNNNN.json
```

Where:
- `CLEANSTART` - Ecosystem identifier
- `YYYY` - 4-digit year
- `LL` - 2 random uppercase letters (e.g., AB, XY, PQ)
- `NNNNN` - 5 random digits (e.g., 12345, 98765)

**Examples:**
- `CLEANSTART-2025-AB12345.json`
- `CLEANSTART-2025-XY98765.json`
- `CLEANSTART-2024-PQ54321.json`

---

## Directory Structure

Files are organized by year:
```
vulnerabilities/
├── 2024/
│   ├── CLEANSTART-2024-AB12345.json
│   └── CLEANSTART-2024-CD67890.json
└── 2025/
    ├── CLEANSTART-2025-EF24680.json
    └── CLEANSTART-2025-GH13579.json
```

---

## JSON Structure

### Simple Format (Minimal Fields)

```json
{
  "schema_version": "1.7.3",
  "id": "CLEANSTART-2025-AB12345",
  "modified": "2025-XX-XXTXX:XX:XXZ",
  "affected": [
    {
      "package": {
        "ecosystem": "CLEANSTART",
        "name": "package_name"
      }
    }
  ]
}
```

### Comprehensive Format (All Fields)

```json
{
  "schema_version": "1.7.3",
  "id": "CLEANSTART-2025-AB12345",
  "modified": "2025-01-15T10:00:00Z",
  "published": "2025-01-15T10:00:00Z",
  "withdrawn": null,
  "aliases": [
    "CVE-2025-8291",
    "BIT-python-2025-8291"
  ],
  "upstream": [
    "CVE-2025-8291"
  ],
  "summary": "Brief description of vulnerability",
  "details": "Detailed multi-paragraph description...",
  "affected": [
    {
      "package": {
        "ecosystem": "CLEANSTART",
        "name": "python3"
      },
      "ranges": [
        {
          "type": "ECOSYSTEM",
          "events": [
            {
              "introduced": "3.9.0"
            },
            {
              "fixed": "3.9.21"
            }
          ]
        }
      ],
      "versions": [
        "3.9.0",
        "3.9.1",
        "3.9.20"
      ]
    }
  ],
  "references": [
    {
      "type": "ADVISORY",
      "url": "https://security.cleanstart.com/advisories/CLEANSTART-2025-AB12345"
    },
    {
      "type": "WEB",
      "url": "https://nvd.nist.gov/vuln/detail/CVE-2025-8291"
    }
  ],
  "severity": [
    {
      "type": "CVSS_V3",
      "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N"
    }
  ]
}
```

---

## OSV Schema Fields Reference

### Required Fields
- `schema_version` - OSV schema version (1.7.3)
- `id` - Unique vulnerability identifier
- `modified` - Last modification timestamp (ISO 8601)

### Core Fields
- `published` - Publication timestamp
- `withdrawn` - Withdrawal timestamp (null if active)
- `aliases` - Array of alternative IDs (CVE, etc.)
- `upstream` - Upstream vulnerability IDs
- `summary` - Brief one-line description
- `details` - Detailed description with markdown

### Affected Package Fields
- `package.ecosystem` - Package ecosystem (CLEANSTART)
- `package.name` - Package name
- `ranges` - Version ranges with introduced/fixed events
- `versions` - Explicit list of affected versions

### Additional Fields
- `references` - Array of URLs (type: ADVISORY/WEB/PACKAGE)
- `severity` - CVSS scores (CVSS_V3)
- `credits` - Vulnerability discoverers/reporters

---

## Quick Start

1. Navigate to project root
2. Run the script:
   ```bash
   python scripts/generate_vulnerability.py
   ```
3. Choose mode:
   - **1** for detailed single file (all fields)
   - **2** for simple single file (minimal)
   - **3** for batch files (simple)
4. Follow the interactive prompts
5. Files are automatically saved to `vulnerabilities/YYYY/`

---

## Tips

- **Mode 1 (Detailed)**: Use for real vulnerabilities with full information
- **Mode 2 (Simple)**: Use for placeholders or when you'll add details later
- **Mode 3 (Batch)**: Use for creating multiple placeholder files quickly
- IDs are randomly generated (2 letters + 5 digits) for unpredictability
- All timestamps are in UTC format (ISO 8601)
- Press Ctrl+D (Linux/Mac) or Ctrl+Z then Enter (Windows) for multiline input
- Or type `.` on a line by itself to finish multiline input

---

## Notes

- Script automatically creates year directories if they don't exist
- IDs use 2 uppercase letters + 5 digits for maximum randomness
- Duplicate ID prevention by checking existing files
- All modes support the CLEANSTART ecosystem
- Comprehensive mode includes all OSV schema fields
- Simple/batch modes create minimal valid records
- You can manually edit JSON files to add more details later

---

## Examples of Valid IDs

```
CLEANSTART-2025-AB12345
CLEANSTART-2025-XY98765
CLEANSTART-2024-PQ54321
CLEANSTART-2024-MN00001
CLEANSTART-2025-ZZ99999
```

Format: Always 2 letters (A-Z) + 5 digits (0-9)

---

## Future Enhancements

Consider adding:
- JSON schema validation script
- Import script for converting from other formats
- Bulk edit script for updating multiple files
- GitHub Actions workflow for automated validation
- Command-line arguments for non-interactive use
- Template system for common vulnerability types
