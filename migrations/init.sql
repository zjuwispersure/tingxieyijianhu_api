-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS dictation
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE dictation;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(32) UNIQUE NOT NULL,
    nickname VARCHAR(32),
    avatar_url VARCHAR(256),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建家庭表
CREATE TABLE IF NOT EXISTS families (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(32) NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户家庭关系表
CREATE TABLE IF NOT EXISTS user_family_relations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    family_id INT NOT NULL,
    role VARCHAR(32) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (family_id) REFERENCES families(id),
    UNIQUE KEY unique_user_family_relation (user_id, family_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建孩子表
CREATE TABLE IF NOT EXISTS children (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    family_id INT NOT NULL,
    child_id INT NOT NULL,
    nickname VARCHAR(80) NOT NULL,
    province VARCHAR(50),
    city VARCHAR(50),
    grade INT,
    semester INT,
    textbook_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (family_id) REFERENCES families(id),
    UNIQUE KEY unique_user_family_child (user_id, family_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建语文条目表
CREATE TABLE IF NOT EXISTS yuwen_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    word VARCHAR(32) NOT NULL,
    pinyin VARCHAR(32),
    type VARCHAR(32),
    unit INT NOT NULL,
    lesson INT NOT NULL,
    lesson_name VARCHAR(32),
    grade INT NOT NULL,
    semester INT NOT NULL,
    textbook_version VARCHAR(32),
    audio_url VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_word_grade_version (word, grade, semester, textbook_version)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建听写任务表
CREATE TABLE IF NOT EXISTS dictation_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    name VARCHAR(32),
    type VARCHAR(32),
    status VARCHAR(32) DEFAULT 'pending',
    total_words INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建听写任务项表
CREATE TABLE IF NOT EXISTS dictation_task_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    yuwen_item_id INT NOT NULL,
    order_num INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dictation_tasks(id),
    FOREIGN KEY (yuwen_item_id) REFERENCES yuwen_items(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建听写会话表
CREATE TABLE IF NOT EXISTS dictation_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    total_words INT,
    correct_count INT DEFAULT 0,
    accuracy_rate FLOAT,
    status VARCHAR(32) DEFAULT 'ongoing',
    time_spent INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dictation_tasks(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建听写详情表
CREATE TABLE IF NOT EXISTS dictation_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    task_item_id INT NOT NULL,
    user_input VARCHAR(32),
    is_correct BOOLEAN,
    time_spent INT,  -- 单词用时(秒)
    retry_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES dictation_sessions(id),
    FOREIGN KEY (task_item_id) REFERENCES dictation_task_items(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建词语学习状态表
CREATE TABLE IF NOT EXISTS word_learning_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_id INT NOT NULL,
    word VARCHAR(32) NOT NULL,
    learning_stage INT DEFAULT 0,
    review_count INT DEFAULT 0,
    next_review DATETIME,
    mastery_level INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id),
    UNIQUE KEY unique_child_word (child_id, word)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建听写配置表
CREATE TABLE IF NOT EXISTS dictation_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    words_per_dictation INT DEFAULT 10,
    review_days INT DEFAULT 3,
    dictation_interval INT DEFAULT 5,
    dictation_ratio INT DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id),
    UNIQUE KEY unique_child_config (child_id)
);

-- 创建索引
-- 用户相关索引
CREATE INDEX idx_user_openid ON users(openid);

-- 家庭相关索引
CREATE INDEX idx_family_created_by ON families(created_by);

-- 用户家庭关系索引
CREATE INDEX idx_user_family_relation ON user_family_relations(user_id, family_id);

-- 孩子相关索引
CREATE INDEX idx_child_user ON children(user_id);
CREATE INDEX idx_child_family ON children(family_id);
CREATE INDEX idx_child_grade ON children(grade, semester);

-- 语文条目索引
CREATE INDEX idx_yuwen_grade ON yuwen_items(grade, semester, unit);
CREATE INDEX idx_yuwen_word ON yuwen_items(word);
CREATE INDEX idx_yuwen_version ON yuwen_items(textbook_version);

-- 听写任务相关索引
CREATE INDEX idx_task_child ON dictation_tasks(child_id);
CREATE INDEX idx_task_status ON dictation_tasks(status);
CREATE INDEX idx_task_type ON dictation_tasks(type);

-- 听写会话相关索引
CREATE INDEX idx_session_task ON dictation_sessions(task_id);
CREATE INDEX idx_session_status ON dictation_sessions(status);
CREATE INDEX idx_session_time ON dictation_sessions(start_time, end_time);

-- 听写详情相关索引
CREATE INDEX idx_detail_session ON dictation_details(session_id);
CREATE INDEX idx_detail_task_item ON dictation_details(task_item_id);
CREATE INDEX idx_detail_correct ON dictation_details(is_correct);

-- 词语学习状态索引
CREATE INDEX idx_learning_status ON word_learning_status(child_id, word, learning_stage);
CREATE INDEX idx_learning_review ON word_learning_status(next_review);

-- 创建家庭成员表
CREATE TABLE IF NOT EXISTS family_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    user_id INT,
    name VARCHAR(32) NOT NULL,
    role VARCHAR(32) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_child BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_user_family (user_id, family_id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE user_achievements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    achievement_type VARCHAR(32) NOT NULL,
    achievement_data JSON,
    level INT DEFAULT 1,
    progress INT DEFAULT 0,
    completed_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(32) NOT NULL,
    content VARCHAR(256),
    type VARCHAR(32),
    is_read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

 