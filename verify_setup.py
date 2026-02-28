"""
Project Setup Verification Script
Verify all dependencies and configurations are correct
"""

import sys
import os

print("=" * 60)
print("EXPENSE TRACKER PRO - SETUP VERIFICATION")
print("=" * 60)

# Check Python version
print("\n✓ Python Version Check")
print(f"  Python Version: {sys.version}")
required_version = (3, 7)
if sys.version_info >= required_version:
    print(f"  ✓ Python 3.7+ is required: PASS")
else:
    print(f"  ✗ Python 3.7+ is required: FAIL")

# Check tkinter
print("\n✓ Tkinter Availability Check")
try:
    import tkinter as tk
    print("  ✓ tkinter is available: PASS")
except ImportError:
    print("  ✗ tkinter NOT found: FAIL")

# Check sqlite3
print("\n✓ SQLite3 Availability Check")
try:
    import sqlite3
    print("  ✓ sqlite3 is available: PASS")
except ImportError:
    print("  ✗ sqlite3 NOT found: FAIL")

# Check project files
print("\n✓ Project Files Check")
required_files = [
    'main.py',
    'config.py',
    'database.py',
    'auth_ui.py',
    'expense_tracker.py',
    'pdf_generator.py',
    'utils.py',
    'requirements.txt',
    'README.md',
    'QUICK_START.md'
]

all_present = True
for file in required_files:
    exists = os.path.isfile(file)
    status = "✓" if exists else "✗"
    print(f"  {status} {file}: {'FOUND' if exists else 'MISSING'}")
    if not exists:
        all_present = False

# Check optional dependencies
print("\n✓ Optional Dependencies Check")
optional_deps = [
    ('reportlab', 'PDF Generation'),
    ('PIL', 'Image Processing'),
    ('dateutil', 'Date Utilities'),
    ('cv2', 'Image Recognition (Optional)')
]

for package, purpose in optional_deps:
    try:
        __import__(package)
        print(f"  ✓ {package}: INSTALLED")
    except ImportError:
        print(f"  ✗ {package}: NOT INSTALLED - {purpose}")

# Summary
print("\n" + "=" * 60)
print("SETUP STATUS")
print("=" * 60)

if all_present:
    print("\n✓ All project files are present!")
    print("\nTo start the application, run:")
    print("  python main.py")
else:
    print("\n✗ Some project files are missing!")
    print("Please ensure all files are in the project directory.")

print("\nFor help, see:")
print("  - README.md for detailed documentation")
print("  - QUICK_START.md for quick start guide")
print("  - .github/copilot-instructions.md for development guide")

print("\n" + "=" * 60)
print("Required packages to install:")
print("=" * 60)
print("\nRun the following command to install dependencies:")
print("  pip install -r requirements.txt")

print("\n" + "=" * 60)
