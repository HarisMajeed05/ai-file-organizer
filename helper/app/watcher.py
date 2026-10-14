"""Watches the folders listed in config.yaml (subfolders included) and organizes files.

Run from the helper folder: python -m app.watcher
"""
import csv
import os
import queue
import shutil
import threading
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import config
from .pipeline import analyze

LOG_HEADER = ["timestamp", "original_path", "new_path", "category", "status", "confidence", "description"]


def out_dir_of(root):
    return root / config.ORGANIZED_FOLDER


@lru_cache(maxsize=4096)
def _is_project_dir(directory):
    return any((Path(directory) / marker).exists() for marker in config.PROJECT_MARKERS)


def should_skip(path, root):
    """True when the file must be left alone."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    if out_dir_of(root) in path.parents:
        return True
    if not config.RECURSIVE and len(rel.parts) > 1:
        return True
    for part in rel.parts[:-1]:
        if part in config.IGNORE_DIRS:
            return True
    if config.IGNORE_HIDDEN and any(part.startswith(".") for part in rel.parts):
        return True
    if path.suffix.lower() in config.IGNORE_EXTENSIONS:
        return True
    if config.PROTECT_PROJECT_DIRS:
        current = path.parent
        while current != root and root in current.parents:
            if _is_project_dir(str(current)):
                return True
            current = current.parent
    return False


def wait_until_stable(path, tries=20):
    """Waits until the file size stops changing (file finished copying or downloading)."""
    last = -1
    for _ in range(tries):
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last and size > 0:
            return True
        last = size
        time.sleep(1)
    return False


def unique_path(dest):
    if not dest.exists():
        return dest
    n = 2
    while dest.with_name(f"{dest.stem}_{n}{dest.suffix}").exists():
        n += 1
    return dest.with_name(f"{dest.stem}_{n}{dest.suffix}")


def write_log(root, row):
    out = out_dir_of(root)
    out.mkdir(parents=True, exist_ok=True)
    log = out / "organizer_log.csv"
    new = not log.exists()
    with open(log, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(LOG_HEADER)
        writer.writerow(row)


def process(path, root):
    if not path.is_file() or should_skip(path, root):
        return
    if not wait_until_stable(path):
        return
    res = analyze(path, path.name, register=not config.DRY_RUN)
    folder = out_dir_of(root) / res["category"]
    if res["subcategory"] and not res["requires_review"]:
        folder = folder / res["subcategory"]
    dest = unique_path(folder / res["final_name"])
    status = "needs_review" if res["requires_review"] else "organized"
    if config.DRY_RUN:
        status = "dry_run_" + status
    else:
        folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
    write_log(root, [datetime.now().isoformat(timespec="seconds"), str(path), str(dest),
                     res["category"], status, res["confidence"], res["description"]])
    print(f"[{status}] {path} -> {dest}")
    if res["requires_review"]:
        print(f"    reason: {res['reason']} | {res['description']}")


def scan_existing(root):
    for current, dirs, files in os.walk(root):
        current = Path(current)
        dirs[:] = [d for d in dirs
                   if d not in config.IGNORE_DIRS and (current / d) != out_dir_of(root)
                   and (config.RECURSIVE)]
        for name in files:
            process(current / name, root)


class Handler(FileSystemEventHandler):
    def __init__(self, jobs):
        self.jobs = jobs

    def on_created(self, event):
        if not event.is_directory:
            self.jobs.put(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.jobs.put(Path(event.dest_path))


def worker(jobs, roots):
    while True:
        path = jobs.get()
        try:
            root = next((r for r in roots if r == path or r in path.parents), None)
            if root:
                process(path, root)
        except Exception as exc:
            print(f"[error] {path}: {type(exc).__name__}: {exc}")
        finally:
            jobs.task_done()


def main():
    roots = []
    for p in config.WATCH_PATHS:
        if p.is_dir():
            roots.append(p.resolve())
        else:
            print(f"Skipping missing folder: {p}")
    if not roots:
        print("No valid folders in watch_paths. Edit config.yaml.")
        return
    print("Mode:", "DRY RUN (nothing is moved)" if config.DRY_RUN else "LIVE")

    jobs = queue.Queue()
    threading.Thread(target=worker, args=(jobs, roots), daemon=True).start()

    if config.SCAN_EXISTING:
        for root in roots:
            print(f"Scanning {root}")
            scan_existing(root)

    observer = Observer()
    for root in roots:
        observer.schedule(Handler(jobs), str(root), recursive=config.RECURSIVE)
        print(f"Watching {root}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
