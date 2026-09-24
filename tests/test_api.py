"""Phase 8 checks via FastAPI's TestClient. No pytest -- run directly:

    python tests/test_api.py

Reads use the real database. The empty-forecasts 404 uses a throwaway schema.
Admin tests never start a job (auth failures and the retrain stub only).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from api.main import app
from config import BASE_DIR, TICKERS
from src.db import get_connection
from src.predict import predict

client = TestClient(app)
SCRATCH = "phase8_test_scratch"


def test_health_and_assets():
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    body = client.get("/assets").json()
    assert "not investment advice" in body["disclaimer"]
    assert [a["ticker"] for a in body["assets"]] == list(TICKERS)
    types = {a["ticker"]: a["asset_type"] for a in body["assets"]}
    assert types["GC=F"] == types["SI=F"] == "futures" and types["INR=X"] == "fx"


def test_forecast_matches_phase6_predict():
    for ticker in TICKERS:
        api = client.get(f"/assets/{ticker}/forecast").json()
        cli = predict(ticker)
        assert api["pred_return_7d"] == cli["pred_return_7d"], ticker
        assert api["as_of"] == cli["as_of"] and api["direction"] == cli["direction"]
        for key in ("model_name", "last_close", "beats_baseline_rmse", "beats_baseline_direction"):
            assert api[key] == cli[key], (ticker, key)
        assert "disclaimer" in api


def test_history_is_capped_and_ascending():
    rows = client.get("/assets/GC=F/history?limit=99999").json()["rows"]
    assert len(rows) == 500
    assert [r["date"] for r in rows] == sorted(r["date"] for r in rows)
    assert client.get("/assets/GC=F/history?limit=3").json()["count"] == 3


def test_metrics_status_and_unknown_ticker():
    m = client.get("/assets/GC=F/metrics").json()
    assert m["model_name"] == "gradient_boosting" and "baseline_mean_rmse" in m["metrics"]
    s = client.get("/status").json()
    assert {"jobs", "forecasts", "prices"} <= set(s)
    assert client.get("/assets/FOO/forecast").status_code == 404


def test_admin_auth_and_retrain_stub():
    os.environ["ADMIN_TOKEN"] = "test-token"
    for path in ("/admin/refresh", "/admin/write-forecasts", "/admin/retrain"):
        assert client.post(path).status_code == 401
        assert client.post(path, headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert client.post("/admin/retrain", headers={"X-Admin-Token": "test-token"}).status_code == 501
    del os.environ["ADMIN_TOKEN"]
    assert client.post("/admin/retrain", headers={"X-Admin-Token": "x"}).status_code == 503


def test_empty_forecasts_table_gives_404():
    base = os.environ["DATABASE_URL"]
    conn = get_connection()
    try:
        conn.execute(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE")
        conn.execute(f"CREATE SCHEMA {SCRATCH}")
        conn.execute(f"SET search_path TO {SCRATCH}")
        conn.execute((BASE_DIR / "schema.sql").read_text())
        os.environ["DATABASE_URL"] = f"{base}?options=-c%20search_path%3D{SCRATCH}"
        r = client.get("/assets/GC=F/forecast")
        assert r.status_code == 404 and "write_forecasts" in r.json()["detail"]
        assets = client.get("/assets").json()["assets"]
        assert all(a["latest_forecast"] is None for a in assets)
    finally:
        os.environ["DATABASE_URL"] = base
        conn.execute("SET search_path TO public")
        conn.execute(f"DROP SCHEMA IF EXISTS {SCRATCH} CASCADE")
        conn.close()


if __name__ == "__main__":
    from src.db import _load_dotenv
    _load_dotenv()
    test_health_and_assets()
    test_forecast_matches_phase6_predict()
    test_history_is_capped_and_ascending()
    test_metrics_status_and_unknown_ticker()
    test_admin_auth_and_retrain_stub()
    test_empty_forecasts_table_gives_404()
    print("All Phase 8 API checks passed.")
