"""P1-07: Model registry & manifest handling."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ModelEntry:
    name: str
    version: str
    path: str
    calibrator_path: str | None
    sha256: str
    metrics: dict
    hyperparameters: dict
    trained_at: str  # ISO8601


def sha256_of(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(models_dir: Path, scaler_meta: dict, entries: list[ModelEntry]) -> None:
    """Write manifest.json containing metadata for all models and the scaler."""
    manifest = {
        "scaler": scaler_meta,
        "models": [asdict(e) for e in entries],
    }
    with (models_dir / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def read_manifest(models_dir: Path) -> dict:
    """Read manifest.json."""
    manifest_path = models_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError("manifest.json not found in models directory.")
    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)
