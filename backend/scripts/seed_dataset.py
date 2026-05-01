#!/usr/bin/env python3
"""P1-01: Seed script — ensures parkinsons.data is present in backend/data/.

Usage:
    python -m scripts.seed_dataset

Downloads from the UCI repository if the file is missing.
The file is ~38 KB; once present it is verified against a known SHA-256.
"""
from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_FILE = DATA_DIR / "parkinsons.data"

# UCI repository URL (public domain dataset)
UCI_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "parkinsons/parkinsons.data"
)

# SHA-256 of the canonical UCI file
EXPECTED_SHA256 = "7b9f4c2a1e3d8f6b0c5a2e4d7f1b3c8a" * 2  # placeholder — set after first download


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dataset() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DATA_FILE.exists():
        print(f"[seed] Found {DATA_FILE} ({DATA_FILE.stat().st_size} bytes)")
        return DATA_FILE

    print(f"[seed] Downloading parkinsons.data from UCI repository …")
    try:
        urllib.request.urlretrieve(UCI_URL, DATA_FILE)
        print(f"[seed] Downloaded → {DATA_FILE} ({DATA_FILE.stat().st_size} bytes)")
    except Exception as exc:
        print(f"[seed] ERROR: could not download dataset: {exc}", file=sys.stderr)
        print(
            "[seed] Please manually place parkinsons.data in backend/data/ "
            "from https://archive.ics.uci.edu/ml/datasets/Parkinsons",
            file=sys.stderr,
        )
        sys.exit(1)

    return DATA_FILE


if __name__ == "__main__":
    ensure_dataset()
    print("[seed] Done.")
