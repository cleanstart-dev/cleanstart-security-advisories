#!/usr/bin/env python3
"""Quick test of auto-fill functionality"""

import sys
sys.path.insert(0, 'scripts')

from generate_vulnerability import fetch_package_data_from_db

# Test with cert-manager
package = "github.com/cert-manager/cert-manager"
print(f"Testing auto-fill for: {package}")
print("=" * 60)

data = fetch_package_data_from_db(package)
if data:
    print("✓ Data found in database:")
    print(f"  Aliases: {data['aliases']}")
    print(f"  Severity: {data['severity']}")
    print(f"  Fixed versions: {data['fixed_versions']}")
    print(f"  Installed versions: {data['installed_versions']}")
    print(f"\nDescription preview:")
    print(data['description'][:200] + "...")
else:
    print("✗ No data found")

