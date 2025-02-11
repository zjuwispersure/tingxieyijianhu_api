-- 设置字符集
SET NAMES utf8mb4;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS dictation
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;

USE dictation;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    openid VARCHAR(64) UNIQUE NOT NULL,
    nickname VARCHAR(32),
    avatar_url VARCHAR(256),
    is_admin BOOLEAN DEFAULT false,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建家庭表
CREATE TABLE IF NOT EXISTS families (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(32) NOT NULL,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建孩子表
CREATE TABLE IF NOT EXISTS children (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    family_id INT NOT NULL,
    child_id INT NOT NULL,
    nickname VARCHAR(32) NOT NULL,
    province VARCHAR(32),
    city VARCHAR(32),
    grade INT,
    semester INT,
    textbook_version VARCHAR(32),
    is_deleted BOOLEAN DEFAULT false NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建听写会话表
CREATE TABLE IF NOT EXISTS dictation_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    child_id INT NOT NULL,
    session_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'in_progress',
    current_word_index INT DEFAULT 0,
    total_words INT DEFAULT 0,
    correct_words INT DEFAULT 0,
    accuracy FLOAT DEFAULT 0.0,
    score FLOAT DEFAULT 0.0,
    total_time INT DEFAULT 0,
    start_time DATETIME,
    end_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (child_id) REFERENCES children(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建听写详情表
CREATE TABLE IF NOT EXISTS dictation_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    yuwen_item_id INT NOT NULL,
    word VARCHAR(100) NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    user_input VARCHAR(100),
    retry_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    last_wrong_time DATETIME,
    time_spent INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES dictation_sessions(id),
    FOREIGN KEY (yuwen_item_id) REFERENCES yuwen_items(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建听写配置表
CREATE TABLE IF NOT EXISTS dictation_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    child_id INT NOT NULL,
    words_per_dictation INT DEFAULT 10,
    review_days INT DEFAULT 3,
    dictation_interval INT DEFAULT 5,
    dictation_ratio INT DEFAULT 100,
    dictation_mode VARCHAR(20) DEFAULT 'unit',
    retry_limit INT DEFAULT 3,
    auto_play BOOLEAN DEFAULT true,
    wrong_words_only BOOLEAN DEFAULT false,
    random_order BOOLEAN DEFAULT false,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建语文词条表
CREATE TABLE IF NOT EXISTS yuwen_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    word VARCHAR(32) NOT NULL,
    pinyin VARCHAR(64),
    hint VARCHAR(128),
    type VARCHAR(32),
    unit VARCHAR(32),
    lesson INT,
    lesson_name VARCHAR(64),
    grade INT,
    semester INT,
    textbook_version VARCHAR(32),
    audio_url VARCHAR(256),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入初始数据
INSERT INTO yuwen_items (word, pinyin, type, unit, lesson, grade, semester, textbook_version) VALUES
('和睦', 'hé mù', '词语', '一单元', 1, 4, 1, '人教版'),
('友爱', 'yǒu ài', '词语', '一单元', 1, 4, 1, '人教版');

-- 添加外键约束和索引
ALTER TABLE children
    ADD CONSTRAINT fk_children_user FOREIGN KEY (user_id) REFERENCES users(id),
    ADD CONSTRAINT fk_children_family FOREIGN KEY (family_id) REFERENCES families(id),
    ADD UNIQUE KEY unique_user_child (user_id, child_id);

ALTER TABLE dictation_sessions
    ADD CONSTRAINT fk_sessions_child FOREIGN KEY (child_id) REFERENCES children(id);

ALTER TABLE dictation_details
    ADD CONSTRAINT fk_details_session FOREIGN KEY (session_id) REFERENCES dictation_sessions(id);

ALTER TABLE dictation_configs
    ADD CONSTRAINT fk_configs_session FOREIGN KEY (session_id) REFERENCES dictation_sessions(id),
    ADD CONSTRAINT fk_configs_child FOREIGN KEY (child_id) REFERENCES children(id);

-- 添加索引
CREATE INDEX idx_users_openid ON users(openid);
CREATE INDEX idx_children_user ON children(user_id);
CREATE INDEX idx_children_family ON children(family_id);
CREATE INDEX idx_sessions_child ON dictation_sessions(child_id);
CREATE INDEX idx_details_session ON dictation_details(session_id);
CREATE INDEX idx_configs_session ON dictation_configs(session_id);
CREATE INDEX idx_configs_child ON dictation_configs(child_id);
CREATE INDEX idx_yuwen_items_word ON yuwen_items(word);
CREATE INDEX idx_yuwen_items_lesson ON yuwen_items(grade, semester, textbook_version, unit, lesson);

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

 