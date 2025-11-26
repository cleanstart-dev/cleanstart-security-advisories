#!/usr/bin/env python3
"""
Export SQLite vulnerability data to OSV JSON format.
This script reads from the SQLite database and creates JSON files
that can be used in your other repository.

Usage:
    python export_sqlite_to_osv_json.py [--output-dir OUTPUT_DIR] [--db-path DB_PATH] [--include-no-cve]
"""

import sqlite3
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

# Default Configuration
DEFAULT_DB_PATH = os.path.abspath("data/vulnstatus.db")
DEFAULT_OUTPUT_DIR = os.path.abspath("exported_osv_data")

def fetch_all_vulnerabilities(db_path, include_no_cve=False):
    """Fetch all vulnerabilities from SQLite database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT folder, image_version, cve, status, notes, library, 
               installed_version, fixed_version, severity, description, updated
        FROM vuln_status
        ORDER BY folder, image_version, cve
    ''')
    results = c.fetchall()
    conn.close()
    
    # Filter out NO_CVE if not requested
    if not include_no_cve:
        results = [r for r in results if r[2] != "NO_CVE"]
    
    return results

def group_by_image(data):
    """Group vulnerabilities by image_version and folder."""
    grouped = {}
    for folder, image_version, cve, status, notes, library, installed_version, fixed_version, severity, description, updated in data:
            
        key = (folder, image_version)
        if key not in grouped:
            grouped[key] = {
                "folder": folder,
                "image_version": image_version,
                "vulnerabilities": []
            }
        
        vuln = {
            "id": cve,
            "cve": cve,
            "severity": severity or "Unknown",
            "package": library or "",
            "library": library or "",
            "installed_version": installed_version or "",
            "fixed_version": fixed_version or "",
            "description": description or "",
            "status": status,
            "notes": notes or "",
            "updated": updated or ""
        }
        grouped[key]["vulnerabilities"].append(vuln)
    
    return grouped

def create_osv_json_format(image_data):
    """Create OSV-compatible JSON format."""
    return {
        "image_name": image_data["image_version"],
        "metadata": {
            "image_name": image_data["image_version"],
            "folder": image_data["folder"],
            "exported_at": datetime.utcnow().isoformat() + "Z"
        },
        "vulnerabilities": image_data["vulnerabilities"]
    }

def export_to_json_files(grouped_data, output_dir):
    """Export grouped data to individual JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    
    exported_files = []
    
    for (folder, image_version), image_data in grouped_data.items():
        # Create OSV format
        osv_data = create_osv_json_format(image_data)
        
        # Create safe filename from image_version
        # Replace special characters that might cause issues in filenames
        safe_name = image_version.replace("/", "_").replace(":", "_").replace("\\", "_")
        filename = f"{safe_name}.json"
        
        # Optionally organize by folder
        if folder:
            folder_path = os.path.join(output_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            filepath = os.path.join(folder_path, filename)
        else:
            filepath = os.path.join(output_dir, filename)
        
        # Write JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(osv_data, f, indent=2, ensure_ascii=False)
        
        exported_files.append(filepath)
        print(f"✓ Exported: {filepath} ({len(image_data['vulnerabilities'])} vulnerabilities)")
    
    return exported_files

def export_single_combined_json(grouped_data, output_dir):
    """Export all data to a single combined JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    combined = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "images": []
    }
    
    for (folder, image_version), image_data in grouped_data.items():
        osv_data = create_osv_json_format(image_data)
        combined["images"].append(osv_data)
    
    filepath = os.path.join(output_dir, "all_vulnerabilities.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported combined file: {filepath}")
    return filepath

def main():
    """Main export function."""
    parser = argparse.ArgumentParser(
        description="Export SQLite vulnerability data to OSV JSON format"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for JSON files (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})"
    )
    parser.add_argument(
        "--include-no-cve",
        action="store_true",
        help="Include images with NO_CVE (no vulnerabilities)"
    )
    parser.add_argument(
        "--no-combined",
        action="store_true",
        help="Skip creating the combined JSON file"
    )
    
    args = parser.parse_args()
    
    db_path = os.path.abspath(args.db_path)
    output_dir = os.path.abspath(args.output_dir)
    
    print("=" * 60)
    print("SQLite to OSV JSON Exporter")
    print("=" * 60)
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Error: Database not found at {db_path}")
        return
    
    print(f"📂 Reading from: {db_path}")
    
    # Fetch all data
    print("📊 Fetching vulnerabilities from database...")
    data = fetch_all_vulnerabilities(db_path, args.include_no_cve)
    print(f"   Found {len(data)} vulnerability records")
    
    if not data:
        print("⚠️  No data found in database. Exiting.")
        return
    
    # Group by image
    print("🔄 Grouping by image...")
    grouped = group_by_image(data)
    print(f"   Found {len(grouped)} unique images")
    
    # Export to individual JSON files
    print(f"\n📤 Exporting to: {output_dir}")
    exported_files = export_to_json_files(grouped, output_dir)
    
    # Also export a combined file unless disabled
    if not args.no_combined:
        export_single_combined_json(grouped, output_dir)
    
    print("\n" + "=" * 60)
    print(f"✅ Export complete!")
    print(f"   - Individual files: {len(exported_files)}")
    print(f"   - Output directory: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()

