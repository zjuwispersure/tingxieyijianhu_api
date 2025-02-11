-- 设置字符集
SET NAMES utf8mb4;
USE dictation;

-- 修改数据库字符集
ALTER DATABASE dictation CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 修改表字符集
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE families CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE children CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE yuwen_items CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 