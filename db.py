"""TiDB Cloud Zero database connection and schema management."""
import pymysql
from urllib.parse import urlparse
from config import settings

_connection = None


def get_connection():
    global _connection
    if _connection and _connection.open:
        return _connection

    parsed = urlparse(settings.tidb_connection_string)
    _connection = pymysql.connect(
        host=parsed.hostname,
        port=parsed.port or 4000,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        ssl={"ca": "/etc/ssl/cert.pem"},  # TiDB Cloud requires SSL (macOS cert path)
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    return _connection


def execute(sql, params=None):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def execute_one(sql, params=None):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def execute_insert(sql, params=None):
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.lastrowid


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    with conn.cursor() as cursor:
        # entries — Impact items logged per day
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                category VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                stakeholders JSON,
                work_type VARCHAR(30),
                delegation_score INT,
                time_estimate VARCHAR(20),
                impact_level VARCHAR(10),
                notes TEXT,
                scope_tag VARCHAR(50),
                scope_response VARCHAR(20),
                escalated_from VARCHAR(100),
                reasoning TEXT,
                source VARCHAR(30) DEFAULT 'manual',
                suggestion_id INT,
                quick_entry TINYINT(1) DEFAULT 0,
                deleted TINYINT(1) DEFAULT 0,
                deleted_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_entries_date (date),
                INDEX idx_entries_deleted (deleted)
            )
        """)

        # daily_meta — Day-level context
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_meta (
                date DATE PRIMARY KEY,
                cognitive_load VARCHAR(1),
                energy VARCHAR(20),
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # raw_events — Ingested data from connectors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                connector_id VARCHAR(30) NOT NULL,
                external_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(50),
                event_date DATE,
                raw_data JSON,
                processed TINYINT(1) DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_connector_event (connector_id, external_id),
                INDEX idx_raw_events_date (event_date),
                INDEX idx_raw_events_processed (processed)
            )
        """)

        # suggestions — AI-generated impact item proposals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                suggested_category VARCHAR(50),
                suggested_description TEXT,
                suggested_stakeholders JSON,
                suggested_work_type VARCHAR(30),
                suggested_delegation_score INT,
                suggested_time_estimate VARCHAR(20),
                suggested_impact_level VARCHAR(10),
                suggested_notes TEXT,
                suggested_scope_tag VARCHAR(50),
                suggested_scope_response VARCHAR(20),
                suggested_escalated_from VARCHAR(100),
                reasoning TEXT,
                confidence FLOAT,
                source_connector VARCHAR(30),
                source_event_ids JSON,
                resolved_entry_id INT,
                updates_suggestion_id INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_suggestions_date (date),
                INDEX idx_suggestions_status (status)
            )
        """)

        # connector_config — Sync status per connector
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connector_config (
                connector_id VARCHAR(30) PRIMARY KEY,
                enabled TINYINT(1) DEFAULT 1,
                last_sync DATETIME,
                config JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # drafts — Form draft auto-save
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id VARCHAR(50) PRIMARY KEY,
                data JSON,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

    print("Database tables initialized.")
