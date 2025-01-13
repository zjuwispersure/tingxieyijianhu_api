-- 为听写相关表添加索引
ALTER TABLE dictation_tasks ADD INDEX idx_task_child (child_id);
ALTER TABLE dictation_tasks ADD INDEX idx_task_status (status);
ALTER TABLE dictation_tasks ADD INDEX idx_task_type (type);

ALTER TABLE dictation_sessions ADD INDEX idx_session_task (task_id);
ALTER TABLE dictation_sessions ADD INDEX idx_session_status (status);
ALTER TABLE dictation_sessions ADD INDEX idx_session_time (start_time, end_time);

ALTER TABLE dictation_details ADD INDEX idx_detail_session (session_id);
ALTER TABLE dictation_details ADD INDEX idx_detail_task_item (task_item_id);
ALTER TABLE dictation_details ADD INDEX idx_detail_correct (is_correct);

-- 为词语学习状态添加复合索引
ALTER TABLE word_learning_status 
ADD INDEX idx_learning_status (child_id, word, learning_stage);

-- 为统计查询添加复合索引
ALTER TABLE dictation_sessions 
ADD INDEX idx_stats_query (child_id, status, created_at); 