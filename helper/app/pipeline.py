"""Validation, extraction, classification and safe naming for one file."""
import hashlib
import re
from pathlib import Path

from . import config, db
from .classifier import classify
from .extractors import extract, kind_of


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_stem(text, fallback):
    text = re.sub(r"[^A-Za-z0-9 _-]", "", str(text or ""))
    text = re.sub(r"[\s-]+", "_", text).strip("_")[:80]
    return text or fallback


def safe_folder(text):
    text = re.sub(r"[^A-Za-z0-9 _-]", "", str(text or "")).strip().replace(" ", "_")
    return text[:40]


def _review(orig, sha, reason, category=config.REVIEW_FOLDER, description=""):
    return {
        "original_filename": orig, "category": category, "subcategory": "",
        "suggested_filename": orig, "final_name": orig, "description": description or reason,
        "confidence": 0.0, "requires_review": True, "reason": reason, "sha256": sha,
    }


def analyze(path, original_name, register=True):
    path = Path(path)
    ext = Path(original_name).suffix.lower()
    stem = Path(original_name).stem
    size = path.stat().st_size
    sha = sha256_of(path)

    if size > config.MAX_FILE_BYTES:
        return _review(original_name, sha, "File exceeds size limit")
    dup = db.find_duplicate(sha)
    if dup:
        return _review(original_name, sha, f"Duplicate of {dup[0]}/{dup[1]}")
    if ext in config.BLOCKED_EXT:
        return _review(original_name, sha, "Executable or binary, not analyzed")

    data = extract(path, ext)
    result = classify(original_name, data)

    category = result.get("category")
    if category not in config.CATEGORIES:
        return _review(original_name, sha, "Model returned a category outside the approved list")
    try:
        confidence = max(0.0, min(1.0, float(result.get("confidence", 0))))
    except (TypeError, ValueError):
        confidence = 0.0

    suggested = safe_stem(result.get("suggested_filename"), safe_stem(stem, "file"))
    needs_review = confidence < config.CONFIDENCE_THRESHOLD or (kind_of(ext) == "other" and category == "Other")
    reason = "Low confidence or unknown type" if needs_review else "OK"
    if needs_review:
        out = _review(original_name, sha, reason, description=result.get("description", ""))
        out["confidence"] = confidence
        out["suggested_filename"] = suggested + ext
        return out

    final_name = db.unique_name(category, suggested + ext)
    if register:
        db.register(sha, category, final_name)
    return {
        "original_filename": original_name, "category": category,
        "subcategory": safe_folder(result.get("subcategory")),
        "suggested_filename": suggested + ext, "final_name": final_name,
        "description": str(result.get("description", ""))[:300],
        "confidence": confidence, "requires_review": False, "reason": reason, "sha256": sha,
    }
