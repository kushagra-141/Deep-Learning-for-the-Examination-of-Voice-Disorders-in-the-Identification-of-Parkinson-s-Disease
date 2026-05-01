"""Integration tests for /batch (P3-06)."""
from __future__ import annotations

import io
import time

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.schemas.feature import VoiceFeatures
from app.services.preprocessing import load_dataset

pytestmark = pytest.mark.integration


def _make_csv(n_rows: int = 3) -> bytes:
    """Take the first n rows of the bundled dataset and serialize to CSV bytes."""
    df = load_dataset(get_settings().DATA_DIR / "parkinsons.data")
    head = df[VoiceFeatures.FEATURE_ORDER].head(n_rows).reset_index(drop=True)
    buf = io.StringIO()
    head.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _wait_for_status(
    client: TestClient,
    job_id: str,
    *,
    target: str,
    timeout_s: float = 5.0,
) -> dict:
    """Poll until the job reaches `target` (or any failed state). Tight loop."""
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        r = client.get(f"/api/v1/batch/{job_id}")
        assert r.status_code == 200, r.text
        last = r.json()
        if last["status"] in (target, "failed"):
            return last
        time.sleep(0.1)
    return last


def test_batch_create_returns_202_with_job_id(client: TestClient) -> None:
    csv_bytes = _make_csv(2)
    r = client.post(
        "/api/v1/batch/",
        files={"file": ("rows.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 202, r.text
    body = r.json()
    assert body["job_id"]
    assert body["status_url"].endswith(body["job_id"])


def test_batch_full_flow_runs_and_returns_csv(client: TestClient) -> None:
    csv_bytes = _make_csv(3)
    r = client.post(
        "/api/v1/batch/",
        files={"file": ("rows.csv", csv_bytes, "text/csv")},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    final = _wait_for_status(client, job_id, target="succeeded", timeout_s=10.0)
    assert final["status"] == "succeeded", final
    assert final["row_count"] == 3
    assert final["progress"] == 1.0

    download = client.get(f"/api/v1/batch/{job_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("text/csv")

    out = pd.read_csv(io.BytesIO(download.content))
    assert len(out) == 3
    for col in ("ensemble_probability", "ensemble_label", "primary_model"):
        assert col in out.columns


def test_batch_unknown_id_404(client: TestClient) -> None:
    r = client.get("/api/v1/batch/not-a-uuid")
    assert r.status_code == 404


def test_batch_download_before_done_returns_409(client: TestClient) -> None:
    """Submit a job and immediately try to download — should 409 if still running.

    Note: with TestClient the background task may already have completed by the
    time we issue the GET, so we accept either 409 (still running) or 200 (done).
    The point of the test is that we never see a 5xx.
    """
    csv_bytes = _make_csv(2)
    r = client.post("/api/v1/batch/", files={"file": ("rows.csv", csv_bytes, "text/csv")})
    job_id = r.json()["job_id"]
    download = client.get(f"/api/v1/batch/{job_id}/download")
    assert download.status_code in (200, 409)


def test_batch_invalid_csv_records_failure(client: TestClient) -> None:
    """A CSV missing required columns must surface as a `failed` status."""
    bad_csv = b"col_a,col_b\n1,2\n3,4\n"
    r = client.post("/api/v1/batch/", files={"file": ("bad.csv", bad_csv, "text/csv")})
    assert r.status_code == 202  # accepted, fails async
    job_id = r.json()["job_id"]
    final = _wait_for_status(client, job_id, target="failed", timeout_s=5.0)
    assert final["status"] == "failed"
    assert final["error"] is not None
