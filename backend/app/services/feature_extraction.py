"""P1-05: Feature extraction from audio files using parselmouth."""
from __future__ import annotations

from typing import Any

import librosa
import numpy as np

# Try importing parselmouth, but allow the app to boot without it for tests/dev
try:
    import parselmouth
    from parselmouth.praat import call
    HAVE_PARSELMOUTH = True
except ImportError:
    HAVE_PARSELMOUTH = False

import structlog
from app.services.nonlinear import d2, dfa, ppe, rpde, spread1, spread2

logger = structlog.get_logger(__name__)


def extract_features_from_audio(path: str, *, target_sr: int = 22_050) -> dict[str, float]:
    """Return the 22-feature dict using Praat via parselmouth."""
    if not HAVE_PARSELMOUTH:
        raise RuntimeError("parselmouth is not installed. Please install praat-parselmouth.")

    logger.info("audio_extraction_start", path=path)
    
    y, sr = librosa.load(path, sr=target_sr, mono=True)
    logger.info("audio_loaded", duration=len(y)/sr, sr=sr)
    
    snd = parselmouth.Sound(y, sr)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
    pp = call(snd, "To PointProcess (periodic, cc)", 75, 600)
    logger.info("praat_objects_created")

    # ── Frequency ──
    fo = call(pitch, "Get mean", 0, 0, "Hertz")
    fhi = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
    flo = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")

    # ── Jitter ──
    jitter_local = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    jitter_local_abs = call(pp, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
    rap = call(pp, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
    ppq = call(pp, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
    ddp = call(pp, "Get jitter (ddp)", 0, 0, 0.0001, 0.02, 1.3)

    # ── Shimmer ──
    shimmer_local = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    shimmer_local_db = call([snd, pp], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq3 = call([snd, pp], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq5 = call([snd, pp], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq = call([snd, pp], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    dda = call([snd, pp], "Get shimmer (dda)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    logger.info("shimmer_done")

    # ── Harmonicity ──
    harmonicity = snd.to_harmonicity_cc()
    hnr = call(harmonicity, "Get mean", 0, 0)
    nhr = 1 / (10 ** (hnr / 10) + 1e-9)  # approximate conversion
    logger.info("harmonicity_done")

    # ── Nonlinear (Stubs/Estimates for MVP) ──
    logger.info("nonlinear_start")
    nl = {
        "RPDE": rpde(y, sr),
        "DFA": dfa(y),
        "spread1": spread1(pitch),
        "spread2": spread2(pitch),
        "D2": d2(y),
        "PPE": ppe(pitch),
    }
    logger.info("nonlinear_done")

    return {
        "MDVP:Fo(Hz)": fo,
        "MDVP:Fhi(Hz)": fhi,
        "MDVP:Flo(Hz)": flo,
        "MDVP:Jitter(%)": jitter_local,
        "MDVP:Jitter(Abs)": jitter_local_abs,
        "MDVP:RAP": rap,
        "MDVP:PPQ": ppq,
        "Jitter:DDP": ddp,
        "MDVP:Shimmer": shimmer_local,
        "MDVP:Shimmer(dB)": shimmer_local_db,
        "Shimmer:APQ3": apq3,
        "Shimmer:APQ5": apq5,
        "MDVP:APQ": apq,
        "Shimmer:DDA": dda,
        "NHR": nhr,
        "HNR": hnr,
        **nl,
    }
