-- Add progress, result, and message columns to task_logs table
-- Run this manually to update existing database schema

ALTER TABLE task_logs
ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS result JSONB,
ADD COLUMN IF NOT EXISTS message VARCHAR;

-- Add comment for documentation
COMMENT ON COLUMN task_logs.progress IS 'Task progress percentage (0-100)';
COMMENT ON COLUMN task_logs.result IS 'Task result data (JSON)';
COMMENT ON COLUMN task_logs.message IS 'Task status message';

-- Create index on progress for faster queries
CREATE INDEX IF NOT EXISTS idx_task_logs_progress ON task_logs(progress);

-- Update existing records to have default values
UPDATE task_logs SET progress = 0 WHERE progress IS NULL;
