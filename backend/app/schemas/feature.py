"""P1-04: VoiceFeatures schema — 22 acoustic features in canonical column order."""
from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class VoiceFeatures(BaseModel):
    """22 acoustic features extracted from a voice recording.

    Field aliases match the UCI dataset column names exactly.
    Ranges are dataset min/max ± 20 % (rounded), validated server-side.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # ── Frequency ─────────────────────────────────────────────────────────────
    mdvp_fo_hz: float = Field(alias="MDVP:Fo(Hz)", ge=50, le=500, examples=[154.23])
    mdvp_fhi_hz: float = Field(alias="MDVP:Fhi(Hz)", ge=50, le=1000, examples=[197.10])
    mdvp_flo_hz: float = Field(alias="MDVP:Flo(Hz)", ge=20, le=500, examples=[116.32])

    # ── Jitter ────────────────────────────────────────────────────────────────
    mdvp_jitter_pct: float = Field(alias="MDVP:Jitter(%)", ge=0, le=0.10, examples=[0.0067])
    mdvp_jitter_abs: float = Field(alias="MDVP:Jitter(Abs)", ge=0, le=0.005, examples=[0.00004])
    mdvp_rap: float = Field(alias="MDVP:RAP", ge=0, le=0.05, examples=[0.0034])
    mdvp_ppq: float = Field(alias="MDVP:PPQ", ge=0, le=0.05, examples=[0.0038])
    jitter_ddp: float = Field(alias="Jitter:DDP", ge=0, le=0.15, examples=[0.0102])

    # ── Shimmer ───────────────────────────────────────────────────────────────
    mdvp_shimmer: float = Field(alias="MDVP:Shimmer", ge=0, le=0.30, examples=[0.029])
    mdvp_shimmer_db: float = Field(alias="MDVP:Shimmer(dB)", ge=0, le=3.0, examples=[0.282])
    shimmer_apq3: float = Field(alias="Shimmer:APQ3", ge=0, le=0.20, examples=[0.0145])
    shimmer_apq5: float = Field(alias="Shimmer:APQ5", ge=0, le=0.20, examples=[0.0179])
    mdvp_apq: float = Field(alias="MDVP:APQ", ge=0, le=0.30, examples=[0.024])
    shimmer_dda: float = Field(alias="Shimmer:DDA", ge=0, le=0.60, examples=[0.0436])

    # ── Harmonicity ───────────────────────────────────────────────────────────
    nhr: float = Field(alias="NHR", ge=0, le=1.0, examples=[0.0162])
    hnr: float = Field(alias="HNR", ge=5, le=40, examples=[22.4])

    # ── Nonlinear ─────────────────────────────────────────────────────────────
    rpde: float = Field(alias="RPDE", ge=0, le=1, examples=[0.4985])
    dfa: float = Field(alias="DFA", ge=0, le=1, examples=[0.7180])
    spread1: float = Field(alias="spread1", ge=-10, le=0, examples=[-5.94])
    spread2: float = Field(alias="spread2", ge=0, le=1, examples=[0.226])
    d2: float = Field(alias="D2", ge=0, le=4, examples=[2.31])
    ppe: float = Field(alias="PPE", ge=0, le=1, examples=[0.207])

    # Canonical column order from the UCI dataset
    FEATURE_ORDER: ClassVar[list[str]] = [
        "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
        "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
        "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5",
        "MDVP:APQ", "Shimmer:DDA",
        "NHR", "HNR",
        "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
    ]

    def to_array(self) -> list[float]:
        """Return features as a flat list in canonical column order."""
        d = self.model_dump(by_alias=True)
        return [d[k] for k in self.FEATURE_ORDER]


# Healthy / Parkinson's reference ranges (10th–90th percentile from dataset)
FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "MDVP:Fo(Hz)":       (107.0, 224.0),
    "MDVP:Fhi(Hz)":      (118.0, 320.0),
    "MDVP:Flo(Hz)":      (70.0,  186.0),
    "MDVP:Jitter(%)":    (0.002, 0.014),
    "MDVP:Jitter(Abs)":  (0.00001, 0.0001),
    "MDVP:RAP":          (0.001, 0.008),
    "MDVP:PPQ":          (0.001, 0.009),
    "Jitter:DDP":        (0.003, 0.023),
    "MDVP:Shimmer":      (0.015, 0.086),
    "MDVP:Shimmer(dB)": (0.148, 0.800),
    "Shimmer:APQ3":      (0.007, 0.044),
    "Shimmer:APQ5":      (0.009, 0.053),
    "MDVP:APQ":          (0.012, 0.076),
    "Shimmer:DDA":       (0.022, 0.133),
    "NHR":               (0.002, 0.170),
    "HNR":               (13.0,  29.0),
    "RPDE":              (0.36,  0.63),
    "DFA":               (0.70,  0.86),
    "spread1":           (-7.4,  -3.6),
    "spread2":           (0.08,  0.45),
    "D2":                (1.9,   3.1),
    "PPE":               (0.08,  0.45),
}
