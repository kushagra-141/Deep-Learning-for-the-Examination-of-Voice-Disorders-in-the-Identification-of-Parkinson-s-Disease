"""P1-10: Models metadata + per-model curves (ROC, PR, calibration)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.core.errors import AppException
from app.services import model_eval

router = APIRouter()


def _manager(request: Request) -> Any:
    return request.app.state.model_manager


@router.get("/models")
async def list_models(request: Request) -> list[dict[str, Any]]:
    """Return every loaded model from the manifest (9 + future ensemble entry)."""
    manager = _manager(request)
    return manager.manifest.get("models", [])


@router.get("/models/compare")
async def compare_models(request: Request) -> dict[str, Any]:
    """Side-by-side metric table across all loaded models."""
    manager = _manager(request)
    return {"models": manager.manifest.get("models", [])}


@router.get("/models/{name}/confusion-matrix")
async def confusion_matrix(name: str, request: Request) -> dict[str, Any]:
    manager = _manager(request)
    try:
        return model_eval.get_confusion_matrix(manager, name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown model '{name}'") from None


@router.get("/models/{name}/roc")
async def roc(name: str, request: Request) -> dict[str, Any]:
    manager = _manager(request)
    try:
        return model_eval.get_roc(manager, name)
    except (KeyError, AppException):
        raise HTTPException(status_code=404, detail=f"Unknown model '{name}'") from None


@router.get("/models/{name}/pr")
async def precision_recall(name: str, request: Request) -> dict[str, Any]:
    manager = _manager(request)
    try:
        return model_eval.get_pr(manager, name)
    except (KeyError, AppException):
        raise HTTPException(status_code=404, detail=f"Unknown model '{name}'") from None


@router.get("/models/{name}/calibration")
async def calibration(name: str, request: Request, n_bins: int = 10) -> dict[str, Any]:
    if n_bins < 3 or n_bins > 50:
        raise HTTPException(status_code=400, detail="n_bins must be between 3 and 50")
    manager = _manager(request)
    try:
        return model_eval.get_calibration(manager, name, n_bins=n_bins)
    except (KeyError, AppException):
        raise HTTPException(status_code=404, detail=f"Unknown model '{name}'") from None
