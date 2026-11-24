-- Apply once to an offline v1 fixture database with all scheduler clients stopped.
BEGIN IMMEDIATE;
ALTER TABLE scheduled_fixture ADD COLUMN priority INTEGER NOT NULL DEFAULT 5 CHECK(priority BETWEEN 0 AND 9);
ALTER TABLE scheduled_fixture ADD COLUMN worker_reserved INTEGER NOT NULL DEFAULT 0 CHECK(worker_reserved IN (0, 1));
-- An old recovery hold did not record whether its original worker returned.
-- Preserve ambiguous capacity use instead of assuming the worker is gone.
UPDATE scheduled_fixture SET worker_reserved = 1
WHERE state = 'RUNNING' OR (state = 'SUPERVISOR_HOLD' AND reason = 'interrupted_claim');
COMMIT;
