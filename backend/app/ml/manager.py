"""P1-07: Model manager — singleton registry for loaded models."""
from __future__ import annotations

import joblib
from pathlib import Path
from typing import Any

from app.ml.registry import read_manifest, sha256_of
from app.core.errors import AppException


class ModelManager:
    """Manages loading and serving of ML models and the scaler."""

    def __init__(self, models_dir: Path) -> None:
        self.models_dir = models_dir
        self.scaler: Any = None
        self.models: dict[str, dict[str, Any]] = {}  # name -> {"model": ..., "version": ..., "calibrator": ...}
        self.manifest: dict | None = None

    @classmethod
    def from_dir(cls, models_dir: Path) -> "ModelManager":
        """Factory method to create and initialize the manager."""
        manager = cls(models_dir)
        manager.load_all()
        return manager

    def load_all(self) -> None:
        """Load manifest, scaler, and all models into memory."""
        if not self.models_dir.exists():
            raise AppException(
                status_code=500,
                code="MODELS_NOT_FOUND",
                message="Models directory does not exist. Run training script first.",
            )

        self.manifest = read_manifest(self.models_dir)

        # Load scaler
        scaler_path = self.models_dir / self.manifest["scaler"]["path"]
        self.scaler = joblib.load(scaler_path)

        # Load models
        for entry in self.manifest["models"]:
            name = entry["name"]
            model_path = self.models_dir / entry["path"]
            
            model_dict = {
                "model": joblib.load(model_path),
                "version": entry["version"],
                "calibrator": None,
                "metadata": entry,
            }

            if entry.get("calibrator_path"):
                calibrator_path = self.models_dir / entry["calibrator_path"]
                model_dict["calibrator"] = joblib.load(calibrator_path)
            
            self.models[name] = model_dict

    def verify_integrity(self) -> None:
        """Verify SHA-256 hashes of all loaded artifacts against the manifest."""
        if not self.manifest:
            raise AppException(status_code=500, code="NOT_LOADED", message="Manager not loaded.")
        
        # Check scaler
        scaler_path = self.models_dir / self.manifest["scaler"]["path"]
        if sha256_of(scaler_path) != self.manifest["scaler"]["sha256"]:
            raise AppException(status_code=500, code="INTEGRITY_ERROR", message="Scaler hash mismatch.")

        # Check models
        for entry in self.manifest["models"]:
            model_path = self.models_dir / entry["path"]
            if sha256_of(model_path) != entry["sha256"]:
                raise AppException(
                    status_code=500, 
                    code="INTEGRITY_ERROR", 
                    message=f"Model hash mismatch for {entry['name']}."
                )

    def get_model(self, name: str) -> dict[str, Any]:
        """Get a loaded model by name."""
        if name not in self.models:
            raise AppException(
                status_code=404,
                code="MODEL_NOT_FOUND",
                message=f"Model {name} not found in registry."
            )
        return self.models[name]

    def get_all_models(self) -> dict[str, dict[str, Any]]:
        """Get all loaded models."""
        return self.models
