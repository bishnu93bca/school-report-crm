CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'user',
    school_udise_code VARCHAR(20),
    is_active TINYINT(1) DEFAULT 1,
    is_verified TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL DEFAULT NULL,
    avatar_url VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    PRIMARY KEY (id)
);

CREATE TABLE login_history (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success TINYINT(1) DEFAULT 1,
    PRIMARY KEY (id),
    KEY idx_user_id (user_id)
);

CREATE TABLE reports (
    id INT NOT NULL AUTO_INCREMENT,
    user_id VARCHAR(100),
    incident_id VARCHAR(50) NOT NULL UNIQUE,
    school_id VARCHAR(20) NOT NULL,
    school_name VARCHAR(255) NOT NULL,
    school_address TEXT,
    contact_number VARCHAR(20),
    equipment_type VARCHAR(50),
    brand VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    issue_description TEXT,
    status ENUM('Open', 'In Progress', 'Resolved') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE schools (
    school_id INT NOT NULL AUTO_INCREMENT,
    udise_code VARCHAR(11) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    pincode VARCHAR(6),
    contact_number VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    PRIMARY KEY (school_id)
);