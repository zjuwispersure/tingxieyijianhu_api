-- 添加新字段
ALTER TABLE yuwen_item 
ADD COLUMN audio_status VARCHAR(20) DEFAULT 'pending' AFTER audio_url;

-- 修改现有字段
ALTER TABLE yuwen_item 
MODIFY COLUMN content TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 

-- 添加新字段（如果需要的话）
ALTER TABLE yuwen_item 
ADD COLUMN IF NOT EXISTS new_field VARCHAR(100) DEFAULT NULL AFTER unit; 