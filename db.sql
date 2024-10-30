CREATE DATABASE blog_db;
USE blog_db;

CREATE TABLE blog_post (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'user'  -- role může být 'user' nebo 'admin'
);

ALTER TABLE blog_post
ADD COLUMN owner_id INT,
ADD COLUMN visibility VARCHAR(20) DEFAULT 'public',
ADD CONSTRAINT FK_owner FOREIGN KEY (owner_id) REFERENCES users(id);

