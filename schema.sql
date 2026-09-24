-- Phase 7 schema. Idempotent: safe to run repeatedly (scripts/migrate.py).
-- Postgres is the source of truth for prices and forecasts.
-- GC=F / SI=F are COMEX futures, not MCX spot. FX volume is indicative only.

CREATE TABLE IF NOT EXISTS ohlcv (
    ticker  text             NOT NULL,
    date    date             NOT NULL,
    open    double precision NOT NULL,
    high    double precision NOT NULL,
    low     double precision NOT NULL,
    close   double precision NOT NULL,
    volume  double precision,               -- NULL / 0 is normal for FX
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS forecasts (
    ticker                    text             NOT NULL,
    as_of                     date             NOT NULL,
    pred_return_7d            double precision NOT NULL,
    direction                 text             NOT NULL,  -- up | down | flat
    model_name                text             NOT NULL,
    last_close                double precision NOT NULL,
    beats_baseline_rmse       boolean          NOT NULL,
    beats_baseline_direction  boolean          NOT NULL,
    created_at                timestamptz      NOT NULL DEFAULT now(),
    PRIMARY KEY (ticker, as_of)
);

CREATE TABLE IF NOT EXISTS model_runs (
    id            bigserial PRIMARY KEY,
    ticker        text        NOT NULL,
    model_name    text        NOT NULL,
    artifact_path text        NOT NULL,
    metrics_json  jsonb       NOT NULL,
    trained_at    timestamptz NOT NULL,
    UNIQUE (ticker, artifact_path, trained_at)   -- record_model_runs is re-runnable
);

CREATE TABLE IF NOT EXISTS job_runs (
    id          bigserial PRIMARY KEY,
    job_name    text        NOT NULL,
    started_at  timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    status      text        NOT NULL,   -- running | ok | error
    message     text
);
