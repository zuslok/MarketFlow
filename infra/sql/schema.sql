-- ===============================
-- MarketFlow Database Schema
-- ===============================

-- 1. SYMBOLS
CREATE TABLE IF NOT EXISTS symbols (
    id              SERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL UNIQUE,   -- BTCUSDT, AAPL
    display_Name    TEXT NOT NULL,          -- Bitcoin / Tether
    asset_type      TEXT NOT NULL,          -- crypto, equity, index, forex
    source          TEXT NOT NULL,          -- binance, yahoo, exchangerate
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. PRICES (time-series)
CREATE TABLE IF NOT EXISTS prices (
    index           BIGSERIAL PRIMARY KEY,
    symbol_id       INT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ NOT NULL,
    open            NUMERIC(18,8),
    high            NUMERIC(18,8),
    low             NUMERIC(18,8),
    close           NUMERIC(18,8) NOT NULL,
    volume          NUMERIC(24,8),
    source          TEXT NOT NULL,
    inserted_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT  uq_symbol_ts UNIQUE (symbol_id, ts)
);

CREATE INDEX IF NOT EXISTS idx_prices_symbol_ts
    ON prices(symbol_id, ts DESC);

-- 3. DAILY METRICS (batch results)
CREATE TABLE IF NOT EXISTS daily_metrics (
    id              BIGSERIAL PRIMARY KEY,
    symbol_id       INT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    ma_20           NUMERIC(18,8),
    ma_50           NUMERIC(18,8),
    rsi_14          NUMERIC(18,8),
    volatility_20   NUMERIC(18,8),
    daily_return    NUMERIC(18,8),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_symbol_date UNIQUE(symbol_id, date)
);

-- 4. ETL JOB TRACKING
CREATE TABLE IF NOT EXISTS etl_jobs (
    id              BIGSERIAL PRIMARY KEY,
    job_type        TEXT NOT NULL,         -- ingest_crypto, calc_daily_metrics
    status          TEXT NOT NULL,         -- pending, running, success, failed
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    error_message   TEXT
);