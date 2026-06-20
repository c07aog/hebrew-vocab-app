-- Adds fields required by the word management screens.
-- Safe to run after the existing tables have been created.

ALTER TABLE words ADD COLUMN japanese_meaning TEXT;
ALTER TABLE words ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
