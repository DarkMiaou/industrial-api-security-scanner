-- Idempotent local upgrade for databases created before IASS-OT lot 5.
-- Fresh databases are created directly from the SQLAlchemy models.

DO $$
BEGIN
    CREATE TYPE gatewayprofile AS ENUM ('VULNERABLE', 'HARDENED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE scanexecutionstatus AS ENUM ('RUNNING', 'COMPLETED', 'PARTIAL', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

ALTER TYPE testtype ADD VALUE IF NOT EXISTS 'OT_COMMAND_AUTHZ';
ALTER TYPE testtype ADD VALUE IF NOT EXISTS 'OT_AUDIT';
ALTER TYPE testtype ADD VALUE IF NOT EXISTS 'OT_RATE_LIMIT';

ALTER TABLE scans ADD COLUMN IF NOT EXISTS target_key VARCHAR(64);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS target_name VARCHAR(255);
ALTER TABLE scans ADD COLUMN IF NOT EXISTS profile gatewayprofile;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS status scanexecutionstatus;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS authorization_confirmed BOOLEAN;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS score INTEGER;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS request_count INTEGER;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS duration_ms INTEGER;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;

UPDATE scans
SET
    target_key = COALESCE(target_key, 'ot-gateway-demo'),
    target_name = COALESCE(target_name, 'Water Pump Gateway'),
    profile = COALESCE(profile, 'VULNERABLE'),
    status = COALESCE(status, 'COMPLETED'),
    authorization_confirmed = COALESCE(authorization_confirmed, FALSE),
    request_count = COALESCE(request_count, 0),
    completed_at = COALESCE(completed_at, scan_date);

ALTER TABLE scans ALTER COLUMN target_key SET DEFAULT 'ot-gateway-demo';
ALTER TABLE scans ALTER COLUMN target_key SET NOT NULL;
ALTER TABLE scans ALTER COLUMN target_name SET DEFAULT 'Water Pump Gateway';
ALTER TABLE scans ALTER COLUMN target_name SET NOT NULL;
ALTER TABLE scans ALTER COLUMN profile SET DEFAULT 'VULNERABLE';
ALTER TABLE scans ALTER COLUMN profile SET NOT NULL;
ALTER TABLE scans ALTER COLUMN status SET DEFAULT 'RUNNING';
ALTER TABLE scans ALTER COLUMN status SET NOT NULL;
ALTER TABLE scans ALTER COLUMN authorization_confirmed SET DEFAULT FALSE;
ALTER TABLE scans ALTER COLUMN authorization_confirmed SET NOT NULL;
ALTER TABLE scans ALTER COLUMN request_count SET DEFAULT 0;
ALTER TABLE scans ALTER COLUMN request_count SET NOT NULL;

ALTER TABLE test_results ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS method VARCHAR(10);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS endpoint VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS ot_impact TEXT;

UPDATE test_results
SET
    title = COALESCE(title, 'Legacy API security result'),
    method = COALESCE(method, 'GET'),
    endpoint = COALESCE(endpoint, '/'),
    ot_impact = COALESCE(ot_impact, 'Not assessed by the legacy scanner');

ALTER TABLE test_results ALTER COLUMN title SET NOT NULL;
ALTER TABLE test_results ALTER COLUMN method SET NOT NULL;
ALTER TABLE test_results ALTER COLUMN endpoint SET NOT NULL;
ALTER TABLE test_results ALTER COLUMN ot_impact SET NOT NULL;

CREATE INDEX IF NOT EXISTS ix_scans_status ON scans (status);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_scans_score_range'
    ) THEN
        ALTER TABLE scans
            ADD CONSTRAINT ck_scans_score_range CHECK (score BETWEEN 0 AND 100);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_scans_request_count'
    ) THEN
        ALTER TABLE scans
            ADD CONSTRAINT ck_scans_request_count CHECK (request_count >= 0);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_scans_duration_ms'
    ) THEN
        ALTER TABLE scans
            ADD CONSTRAINT ck_scans_duration_ms CHECK (duration_ms >= 0);
    END IF;
END
$$;
