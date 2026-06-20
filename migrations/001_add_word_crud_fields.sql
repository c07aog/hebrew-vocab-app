-- Adds fields required by the word management screens.
-- SQLite cannot add a column with DEFAULT CURRENT_TIMESTAMP to an existing table,
-- so timestamp columns are added without a non-constant default and then backfilled.

ALTER TABLE words ADD COLUMN japanese_meaning TEXT;
ALTER TABLE words ADD COLUMN updated_at TEXT;

UPDATE words
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
WHERE updated_at IS NULL;
