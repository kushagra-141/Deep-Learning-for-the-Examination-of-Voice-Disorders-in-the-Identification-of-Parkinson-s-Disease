"""Audio endpoint."""
from __future__ import annotations

import os
import tempfile

import structlog
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.rate_limit import limiter
from app.repositories.prediction import create_prediction
from app.schemas.feature import VoiceFeatures
from app.schemas.prediction import PredictionResponse
from app.services.feature_extraction import extract_features_from_audio
from app.services.prediction_service import run_prediction

logger = structlog.get_logger(__name__)
router = APIRouter()
_settings = get_settings()

ALLOWED_MIME_TYPES = {
    "audio/wav", 
    "audio/x-wav", 
    "audio/webm", 
    "audio/ogg", 
    "audio/flac",
    "video/webm", # Sometimes Chrome records webm audio with video mime type
}

@router.post("/predict", response_model=PredictionResponse)
@limiter.limit(f"{_settings.RL_AUDIO_PER_MIN}/minute")
async def predict_audio(
    request: Request,
    db: SessionDep,
    file: UploadFile = File(...),
) -> PredictionResponse:
    """Predict Parkinson's directly from an audio file with strict validation."""
    settings = get_settings()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
        
    if file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning("invalid_mime_type", content_type=file.content_type)
        raise HTTPException(
            status_code=415, 
            detail=f"Unsupported media type: {file.content_type}. Must be wav, webm, ogg, or flac."
        )

    manager = request.app.state.model_manager
    
    original_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".wav"
    ext = original_ext if original_ext in (".wav", ".flac", ".ogg", ".webm") else ".wav"
    
    # Secure temporary file creation
    fd, tmp_path = tempfile.mkstemp(suffix=ext)
    
    try:
        # Stream chunks to prevent OOM
        bytes_read = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with os.fdopen(fd, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > settings.AUDIO_MAX_BYTES:
                    raise HTTPException(
                        status_code=413, 
                        detail=f"File exceeds maximum allowed size of {settings.AUDIO_MAX_BYTES / (1024*1024)}MB."
                    )
                buffer.write(chunk)
                
        if bytes_read == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Extract features
        features_dict = extract_features_from_audio(tmp_path)
        features = VoiceFeatures(**features_dict)

        # Predict + persist
        response = run_prediction(features, manager, input_mode="audio")
        rows = [
            {
                "model_name": m.model_name,
                "model_version": m.model_version,
                "probability": m.probability,
                "label": m.label,
                "shap_values": (
                    {"top": [c.model_dump() for c in m.shap_top]} if m.shap_top else None
                ),
            }
            for m in [*response.per_model, response.ensemble]
        ]
        pred = await create_prediction(
            db,
            features=features.model_dump(by_alias=True),
            input_mode="audio",
            predictions=rows,
        )
        response.prediction_id = str(pred.id)
        response.created_at = pred.created_at.isoformat()
        return response
        
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error("audio_processing_runtime_error", error=str(e))
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error("audio_processing_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Audio processing failed. File may be corrupted or in an unsupported format.")
    finally:
        # Secure cleanup
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception as cleanup_error:
            logger.error("tmp_cleanup_failed", path=tmp_path, error=str(cleanup_error))

