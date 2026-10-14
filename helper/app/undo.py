"""Moves files back to their original locations using the organizer log.

Run from the helper folder: python -m app.undo "C:/path/to/watched/folder"
"""
import csv
import shutil
import sys
from pathlib import Path

from . import config


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m app.undo "<watched folder>"')
        return
    log = Path(sys.argv[1]) / config.ORGANIZED_FOLDER / "organizer_log.csv"
    if not log.exists():
        print("No log found")
        return
    with open(log, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in reversed(rows):
        if row["status"].startswith("dry_run"):
            continue
        src, dst = Path(row["new_path"]), Path(row["original_path"])
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"Restored {dst}")
    log.unlink()


if __name__ == "__main__":
    main()
