from pathlib import Path
import os
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

print()
print("=" * 70)
print("CHOPPED FANTASY FOOTBALL - MASTER RUNNER")
print("=" * 70)

print()
print("STEP 1 - SYNCING ESPN DATA")
print("=" * 70)

result = subprocess.run(
    [sys.executable, "chopped_week.py"]
)

if result.returncode != 0:
    print()
    print("ERROR: ESPN sync failed.")
    raise SystemExit(1)


print()
print("=" * 70)
print("STEP 2 - RUNNING ELIMINATION ENGINE")
print("=" * 70)

result = subprocess.run(
    [sys.executable, "chopped_elimination.py"]
)

if result.returncode != 0:
    print()
    print("ERROR: Elimination engine failed.")
    raise SystemExit(1)


print()
print("=" * 70)
print("CHOPPED RUN COMPLETE")
print("=" * 70)
print()
