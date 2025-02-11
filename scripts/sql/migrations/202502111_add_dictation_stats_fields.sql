-- 添加 dictation_sessions 新字段
ALTER TABLE dictation_sessions
ADD COLUMN score FLOAT DEFAULT 0.0,
ADD COLUMN total_time INT DEFAULT 0;

-- 添加 dictation_details 新字段
ALTER TABLE dictation_details
MODIFY word VARCHAR(100) NOT NULL,
MODIFY user_input VARCHAR(100),
ADD COLUMN retry_count INT DEFAULT 0,
ADD COLUMN error_count INT DEFAULT 0,
ADD COLUMN last_wrong_time DATETIME,
ADD COLUMN time_spent INT DEFAULT 0; 