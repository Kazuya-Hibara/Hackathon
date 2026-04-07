"""Database connection — TiDB Cloud Zero with SQLite in-memory fallback for demo."""
import sqlite3
import pymysql
from urllib.parse import urlparse
from config import settings

_connection = None
_use_sqlite = False


def _is_sqlite():
    return _use_sqlite


def get_connection():
    global _connection, _use_sqlite

    if _use_sqlite:
        if _connection is None:
            _connection = sqlite3.connect(":memory:", check_same_thread=False)
            _connection.row_factory = sqlite3.Row
        return _connection

    if _connection and _connection.open:
        return _connection

    if not settings.tidb_connection_string:
        # Fallback to SQLite demo mode
        _use_sqlite = True
        return get_connection()

    parsed = urlparse(settings.tidb_connection_string)
    try:
        _connection = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 4000,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip("/"),
            ssl={"ca": "/etc/ssl/cert.pem"},
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
    except Exception:
        # If TiDB connection fails, fallback to SQLite
        _use_sqlite = True
        return get_connection()

    return _connection


def _convert_sql(sql):
    """Convert MySQL-style SQL to SQLite-compatible SQL."""
    if not _use_sqlite:
        return sql
    # %s → ?
    sql = sql.replace("%s", "?")
    return sql


def execute(sql, params=None):
    conn = get_connection()
    sql = _convert_sql(sql)
    if _use_sqlite:
        cursor = conn.execute(sql, params or [])
        cols = [d[0] for d in cursor.description] if cursor.description else []
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    else:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def execute_one(sql, params=None):
    conn = get_connection()
    sql = _convert_sql(sql)
    if _use_sqlite:
        cursor = conn.execute(sql, params or [])
        row = cursor.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in cursor.description]
        return dict(zip(cols, row))
    else:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def execute_insert(sql, params=None):
    conn = get_connection()
    sql = _convert_sql(sql)
    if _use_sqlite:
        cursor = conn.execute(sql, params or [])
        conn.commit()
        return cursor.lastrowid
    else:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.lastrowid


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()

    if _use_sqlite:
        _init_sqlite(conn)
        return

    with conn.cursor() as cursor:
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connector_config (
                connector_id VARCHAR(30) PRIMARY KEY,
                enabled TINYINT(1) DEFAULT 1,
                last_sync DATETIME,
                config JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id VARCHAR(50) PRIMARY KEY,
                data JSON,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

    print("Database tables initialized.")


def _init_sqlite(conn):
    """Initialize SQLite schema and seed demo data."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            stakeholders TEXT,
            work_type TEXT,
            delegation_score INTEGER,
            time_estimate TEXT,
            impact_level TEXT,
            notes TEXT,
            scope_tag TEXT,
            scope_response TEXT,
            escalated_from TEXT,
            reasoning TEXT,
            source TEXT DEFAULT 'manual',
            suggestion_id INTEGER,
            quick_entry INTEGER DEFAULT 0,
            deleted INTEGER DEFAULT 0,
            deleted_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS daily_meta (
            date TEXT PRIMARY KEY,
            cognitive_load TEXT,
            energy TEXT,
            summary TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS raw_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            connector_id TEXT NOT NULL,
            external_id TEXT NOT NULL,
            event_type TEXT,
            event_date TEXT,
            raw_data TEXT,
            processed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(connector_id, external_id)
        );
        CREATE TABLE IF NOT EXISTS suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            suggested_category TEXT,
            suggested_description TEXT,
            suggested_stakeholders TEXT,
            suggested_work_type TEXT,
            suggested_delegation_score INTEGER,
            suggested_time_estimate TEXT,
            suggested_impact_level TEXT,
            suggested_notes TEXT,
            suggested_scope_tag TEXT,
            suggested_scope_response TEXT,
            suggested_escalated_from TEXT,
            reasoning TEXT,
            confidence REAL,
            source_connector TEXT,
            source_event_ids TEXT,
            resolved_entry_id INTEGER,
            updates_suggestion_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS connector_config (
            connector_id TEXT PRIMARY KEY,
            enabled INTEGER DEFAULT 1,
            last_sync TEXT,
            config TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            data TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # Check if demo data already seeded
    cursor = conn.execute("SELECT COUNT(*) as c FROM entries")
    if cursor.fetchone()[0] > 0:
        print("Database tables initialized (SQLite demo mode, data exists).")
        return

    _seed_demo_data(conn)
    print("Database tables initialized (SQLite demo mode, demo data seeded).")


def _seed_demo_data(conn):
    """Seed hardcoded demo data for TEAMZ Tokyo hackathon manager."""
    import json
    from datetime import date, timedelta

    TODAY = date.today().isoformat()
    YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
    TWO_DAYS_AGO = (date.today() - timedelta(days=2)).isoformat()

    # Connector config
    for cid in ["slack", "gcal", "bright_data", "claude_code"]:
        conn.execute(
            "INSERT INTO connector_config (connector_id, enabled, last_sync) VALUES (?, 1, datetime('now'))",
            (cid,),
        )

    # Daily Meta
    daily_meta = [
        (TODAY, "M", "STRATEGIC", "Hackathon day! High energy, lots of moving parts."),
        (YESTERDAY, "H", "REACTIVE", "Pre-hackathon chaos. 14 sponsors calling about booth setup."),
        (TWO_DAYS_AGO, "L", "STRATEGIC", "Calm before the storm. Finalized judging criteria."),
    ]
    for d, load, energy, summary in daily_meta:
        conn.execute(
            "INSERT INTO daily_meta (date, cognitive_load, energy, summary) VALUES (?, ?, ?, ?)",
            (d, load, energy, summary),
        )

    # Entries
    entries = [
        (TODAY, "DECISION", "Decided to extend hackathon deadline by 30min after 3 teams requested more time",
         json.dumps(["Yuki", "Sponsors"]), "strategic", 1, "30m", "HIGH", "CORE_ROLE", None, None,
         "Sometimes the best management move is knowing when to flex the rules"),
        (TODAY, "ALIGNMENT", "Morning sync with all 7 sponsor reps — confirmed API keys, booth layout, and judging slots",
         json.dumps(["Zeabur", "Agnes AI", "TiDB", "Bright Data", "Mem9", "Nosana", "QoderWork"]),
         "coordination", 3, "1h", "HIGH", "CORE_ROLE", None, None, None),
        (TODAY, "FIRES_HANDLED", "WiFi went down in Hall B during hackathon kickoff. Coordinated with venue IT, got backup hotspot running in 8 minutes",
         json.dumps(["Venue IT", "Participants"]), "reactive", 1, "15m", "HIGH", "CORE_ROLE", None, None,
         "Personal record for WiFi crisis resolution. Previous best: 12 minutes at ETH Tokyo."),
        (TODAY, "BLOCKER_REMOVED", "Team 'Crypto Cats' couldn't connect to TiDB — walked them through SSL cert setup on Windows",
         json.dumps(["Team Crypto Cats"]), "support", 2, "20m", "MEDIUM", "ADJACENT_OPS", "ADVISORY", "Yuki",
         "Note to self: add Windows SSL guide to next hackathon starter kit"),
        (YESTERDAY, "STRUCTURE", "Created sponsor integration checklist template — 7 sponsors × 4 touchpoints = 28 items tracked",
         json.dumps(["Operations Team"]), "proactive", 4, "2h", "HIGH", "CORE_ROLE", None, None,
         "This template will save ~3h per hackathon going forward"),
        (YESTERDAY, "ALIGNMENT", "1:1 with Tanaka-san (VP) about Q3 event roadmap. Secured budget for 2 more hackathons",
         json.dumps(["Tanaka-san"]), "strategic", 1, "45m", "HIGH", "CORE_ROLE", None, None, None),
        (YESTERDAY, "FIRES_HANDLED", "Discovered catering order was for 100 people, not 200. Emergency call to vendor, upgraded order with 2h to spare",
         json.dumps(["Catering Vendor", "Yuki"]), "reactive", 1, "30m", "HIGH", "BAU_OVERHEAD", "ABSORBED", None,
         "The hero we needed. Also, always triple-check headcount."),
        (YESTERDAY, "TEAM_DEV", "Coached Yuki on sponsor relationship management — she handled 3 sponsor calls independently after",
         json.dumps(["Yuki"]), "coaching", 2, "1h", "MEDIUM", "CORE_ROLE", None, None, None),
        (YESTERDAY, "STRATEGIC_ANTICIPATION", "Noticed 60% of registered teams are solo developers — adjusted judging criteria to not penalize team size",
         None, "proactive", 1, "30m", "MEDIUM", "CORE_ROLE", None, None,
         "Data-driven decision. Last hackathon, solo devs scored 15% lower on average."),
        (TWO_DAYS_AGO, "DECISION", "Selected Happo-en as venue over 3 alternatives — best WiFi infrastructure and garden vibes for networking",
         json.dumps(["Venue Committee"]), "strategic", 1, "1h", "HIGH", "CORE_ROLE", None, None,
         "Gardens > fluorescent-lit conference rooms for creative energy"),
        (TWO_DAYS_AGO, "STRUCTURE", "Drafted judging rubric: 25% MVP completion, 25% Innovation, 25% Real-world relevance, 25% Sponsor tech usage",
         json.dumps(["Judges Panel"]), "proactive", 3, "1.5h", "HIGH", "CORE_ROLE", None, None, None),
        (TWO_DAYS_AGO, "ALIGNMENT", "Cross-team standup with marketing, ops, and partnerships. Aligned on social media coverage plan",
         json.dumps(["Marketing", "Ops", "Partnerships"]), "coordination", 2, "30m", "MEDIUM", "CORE_ROLE", None, None, None),
    ]
    for e in entries:
        conn.execute(
            """INSERT INTO entries (date, category, description, stakeholders, work_type,
               delegation_score, time_estimate, impact_level, scope_tag, scope_response,
               escalated_from, notes, source)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual')""",
            e,
        )

    # Suggestions
    suggestions = [
        (TODAY, "TEAM_DEV", "Recognized Yuki's growth in sponsor management — she independently handled 3 sponsor escalations today",
         json.dumps(["Yuki"]), "coaching", 3, "15m", "MEDIUM", "CORE_ROLE", None, None,
         "Slack data shows Yuki resolved 3 sponsor DMs without escalating. This is a coaching win from yesterday's 1:1.", 0.88),
        (TODAY, "STRATEGIC_ANTICIPATION", "Identified opportunity to create 'Hackathon-in-a-Box' template from today's learnings for Q3 events",
         None, "proactive", 4, "N/A", "HIGH", "STRATEGIC_INITIATIVE", None, None,
         "The sponsor checklist + judging rubric + venue requirements could be packaged. 3 hackathons planned in Q3.", 0.75),
        (TODAY, "ALIGNMENT", "Post-hackathon debrief with judges — collect feedback on scoring rubric effectiveness",
         json.dumps(["Judges Panel"]), "coordination", 2, "30m", "MEDIUM", "CORE_ROLE", None, None,
         "Calendar shows judging ends at 17:30. A 30-min debrief while impressions are fresh would be valuable.", 0.82),
        (TODAY, "BLOCKER_REMOVED", "Created quick-start guide for Windows users connecting to TiDB Cloud Zero (SSL cert setup)",
         json.dumps(["Future Participants"]), "proactive", 4, "30m", "MEDIUM", "ADJACENT_OPS", "TRADEOFF", None,
         "3 teams hit this issue today. A 30-min doc now saves hours at next hackathon.", 0.70),
    ]
    for s in suggestions:
        conn.execute(
            """INSERT INTO suggestions
               (date, suggested_category, suggested_description, suggested_stakeholders,
                suggested_work_type, suggested_delegation_score, suggested_time_estimate,
                suggested_impact_level, suggested_scope_tag, suggested_scope_response,
                suggested_escalated_from, reasoning, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            s,
        )

    # Raw events
    raw_events = [
        ("slack", "slack_001", "message", TODAY,
         json.dumps({"channel": "#hackathon-ops", "from": "Yuki", "text": "WiFi is down in Hall B! Teams are panicking", "ts": "10:15"})),
        ("slack", "slack_002", "message", TODAY,
         json.dumps({"channel": "#hackathon-ops", "from": "Manager", "text": "On it. Contacting venue IT now. ETA 10 min.", "ts": "10:16"})),
        ("slack", "slack_003", "message", TODAY,
         json.dumps({"channel": "#sponsors", "from": "TiDB Rep", "text": "Teams are having SSL issues connecting to Cloud Zero from Windows.", "ts": "11:30"})),
        ("gcal", "gcal_001", "event", TODAY,
         json.dumps({"subject": "TEAMZ AI Hackathon — Main Event", "start": "13:00", "end": "18:00", "location": "Happo-en, Minato City"})),
        ("gcal", "gcal_002", "event", TODAY,
         json.dumps({"subject": "Morning Sponsor Sync", "start": "09:00", "end": "10:00"})),
    ]
    for connector, ext_id, etype, edate, data in raw_events:
        conn.execute(
            """INSERT INTO raw_events (connector_id, external_id, event_type, event_date, raw_data, processed)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (connector, ext_id, etype, edate, data),
        )

    conn.commit()
