-- 创建英语条目表
CREATE TABLE IF NOT EXISTS english_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(64),                    -- 单词/句子内容
    phonetic TEXT,                        -- 音标
    translation TEXT,                     -- 翻译/释义
    type VARCHAR(32),                     -- 类型（单词/句子）
    unit INT,                             -- 单元
    lesson INT,                           -- 课次
    lesson_name VARCHAR(128),             -- 单元名
    grade INT,                            -- 年级
    semester INT,                         -- 学期
    textbook_version VARCHAR(32),         -- 教材版本
    audio_url VARCHAR(256),               -- 音频URL
    audio_status VARCHAR(32) DEFAULT 'pending',  -- 音频状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建英语听写记录表
CREATE TABLE IF NOT EXISTS english_dictation_record (
    id INT AUTO_INCREMENT PRIMARY KEY,
    english_item_id INT NOT NULL,
    family_member_id INT NOT NULL,
    score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (english_item_id) REFERENCES english_items(id),
    FOREIGN KEY (family_member_id) REFERENCES family_member(id)
); 