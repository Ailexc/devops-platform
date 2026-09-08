-- Cloud Manager 初始化 SQL
-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS cloud_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 授权
GRANT ALL PRIVILEGES ON cloud_manager.* TO 'root'@'%';
FLUSH PRIVILEGES;
