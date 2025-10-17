# JSON Validator

This directory contains a JSON schema to validate OSV entries.

## Schema File

- **Schema**: `osv-schema-1.7.3.json`
- **Location**: `schemas/osv-schema-1.7.3.json`
- **Version**: OSV Schema 1.7.3
- **Purpose**: Validates CleanStart vulnerability records for OSV compliance

## Example Usage

### Method 1: Using check-jsonschema (Python)

**Installation:**
```bash
pip install check-jsonschema
```

**Validate single file:**
```bash
check-jsonschema --schemafile schemas/osv-schema-1.7.3.json vulnerabilities/2025/CLEANSTART-2025-AB12345.json
```

**Validate multiple files:**
```bash
check-jsonschema --schemafile schemas/osv-schema-1.7.3.json vulnerabilities/2025/*.json
```

**Validate all vulnerabilities:**
```bash
find vulnerabilities/ -name "*.json" -exec check-jsonschema --schemafile schemas/osv-schema-1.7.3.json {} \;
```

### Method 2: Using yajsv (Go)

**Installation:**
```bash
go install github.com/neilpa/yajsv@latest
```

**Validate single file:**
```bash
yajsv -s schemas/osv-schema-1.7.3.json vulnerabilities/2025/CLEANSTART-2025-AB12345.json
```

**Validate multiple files:**
```bash
yajsv -s schemas/osv-schema-1.7.3.json vulnerabilities/2025/*.json
```

### Method 3: Using Python json-schema library

**Installation:**
```bash
pip install jsonschema
```

**Python script example:**
```python
import json
import jsonschema
from jsonschema import validate

# Load schema
with open('schemas/osv-schema-1.7.3.json', 'r') as f:
    schema = json.load(f)

# Load vulnerability file
with open('vulnerabilities/2025/CLEANSTART-2025-AB12345.json', 'r') as f:
    vulnerability = json.load(f)

# Validate
try:
    validate(instance=vulnerability, schema=schema)
    print("✅ Valid OSV record")
except jsonschema.exceptions.ValidationError as e:
    print(f"❌ Validation error: {e.message}")
```

## Validation Script

A comprehensive validation script is available at:
- **Script**: `scripts/validate.py`
- **Usage**: `python scripts/validate.py [vulnerability_file.json]`

## What Gets Validated

The schema validates:

### Required Fields
- `id` - Unique vulnerability identifier
- `modified` - Last modification timestamp
- `schema_version` - OSV schema version

### Optional Fields
- `published` - Publication timestamp
- `withdrawn` - Withdrawal timestamp
- `aliases` - Alternative identifiers (CVE, etc.)
- `upstream` - Upstream vulnerability references
- `summary` - Brief description
- `details` - Detailed description
- `affected` - Affected packages and versions
- `references` - Related URLs
- `severity` - CVSS scores
- `credits` - Vulnerability discoverers

### CleanStart-Specific Rules
- ID format: `CLEANSTART-YYYY-LLNNNNN`
- Ecosystem: `CLEANSTART`
- Timestamp format: ISO 8601
- Version ranges: Proper introduced/fixed events

## Common Validation Errors

### 1. Invalid ID Format
```
❌ Error: ID must match pattern CLEANSTART-YYYY-LLNNNNN
✅ Fix: Use format like CLEANSTART-2025-AB12345
```

### 2. Missing Required Fields
```
❌ Error: 'id' is a required property
✅ Fix: Ensure all required fields are present
```

### 3. Invalid Timestamp Format
```
❌ Error: Timestamp must be ISO 8601 format
✅ Fix: Use format like 2025-01-15T10:00:00Z
```

### 4. Invalid CVSS Score
```
❌ Error: CVSS score format invalid
✅ Fix: Use proper CVSS vector string
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Validate OSV Records
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install check-jsonschema
      - name: Validate OSV records
        run: |
          find vulnerabilities/ -name "*.json" -exec check-jsonschema --schemafile schemas/osv-schema-1.7.3.json {} \;
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-osv
        name: Validate OSV records
        entry: check-jsonschema --schemafile schemas/osv-schema-1.7.3.json
        language: system
        files: \.json$
        pass_filenames: true
```

## Troubleshooting

### Schema Not Found
```bash
# Ensure you're in the project root directory
cd cleanstart-security-advisories-trial1
check-jsonschema --schemafile schemas/osv-schema-1.7.3.json vulnerabilities/2025/*.json
```

### Permission Issues
```bash
# Make sure the schema file is readable
chmod 644 schemas/osv-schema-1.7.3.json
```

### Multiple Validation Errors
```bash
# Validate files one by one to identify specific issues
for file in vulnerabilities/2025/*.json; do
  echo "Validating $file"
  check-jsonschema --schemafile schemas/osv-schema-1.7.3.json "$file"
done
```

## Best Practices

1. **Validate Before Committing**: Always validate locally before pushing
2. **Use Automated Validation**: Set up CI/CD to validate on every commit
3. **Fix Errors Immediately**: Don't let validation errors accumulate
4. **Test Schema Updates**: Validate existing records when schema changes
5. **Document Changes**: Keep validation documentation up to date

## Support

For validation issues:
- Check the [OSV Schema Documentation](https://ossf.github.io/osv-schema/)
- Review the [OSV Schema Repository](https://github.com/ossf/osv-schema)
- Contact: security@cleanstart.com
