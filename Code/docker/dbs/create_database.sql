-- create_database.sql

-- 1) Extensión
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2) Crear tabla models (si no existe)
CREATE TABLE IF NOT EXISTS models (
    model_id       SERIAL PRIMARY KEY,
    model_name     VARCHAR(255) NOT NULL,
    model_version  INTEGER      NOT NULL,
    mlflow_run_id  VARCHAR(255),
    created_at     TIMESTAMPTZ  DEFAULT NOW(),
    parameters     JSONB,
    metrics        JSONB,
    UNIQUE(model_name, model_version)
);

-- 3) Crear tabla predictions
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id    SERIAL PRIMARY KEY,
    model_id         INTEGER      REFERENCES models(model_id),
    prediction_time  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    input_data       JSONB,
    prediction_value FLOAT        NOT NULL
);

-- 4) Convertir predictions en hypertable
SELECT create_hypertable(
    'predictions',
    'prediction_time',
    if_not_exists => TRUE
);
