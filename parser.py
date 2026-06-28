import re
import json
import sqlite3

# ==============================================================================
# 00. GLOBAL CONFIGURATIONS & REGEX PATTERNS
# ==============================================================================
# Robust Regular Expression to extract core elements from the raw log strings safely
LOG_PATTERN = (
    r"^(?P<timestamp>[\d:\-,\s]+) - "
    r"SERVICE:(?P<service>\w+) - "
    r"LEVEL:(?P<level>\w+) - "
    r"MSG:(?P<message>.*)$"
)


# ==============================================================================
# 01. CORE METADATA EXTRACTION PIPELINE
# ==============================================================================
def extract_metadata(message_text: str) -> dict:
    """
    Parses unstructured sub-details out of the log message string using Regex.
    
    Looks for HTTP status codes, routing targets, query execution times, 
    and raw SQL strings. Returns a structured metadata dictionary.
    """
    metadata = {}
    
    # 1. Capture HTTP Status Codes (e.g., 'Status: 500')
    status_match = re.search(r"Status:\s*(\d+)", message_text)
    if status_match:
        metadata["http_status"] = int(status_match.group(1))
        
    # 2. Capture Network Resource Paths (e.g., 'Target: /api/v1/checkout')
    url_match = re.search(r"Target:\s*([^\s|]+)", message_text)
    if url_match:
        metadata["target_url"] = url_match.group(1)
        
    # 3. Capture Database Execution Durations (e.g., 'Duration: 1.25s')
    duration_match = re.search(r"Duration:\s*([\d.]+)s", message_text)
    if duration_match:
        metadata["query_duration_seconds"] = float(duration_match.group(1))
        
    # 4. Capture Raw SQL Statements (e.g., 'Query: SELECT * FROM users')
    sql_match = re.search(r"Query:\s*(.*)$", message_text)
    if sql_match:
        metadata["raw_sql"] = sql_match.group(1).strip()
        
    return metadata


# ==============================================================================
# 02. DATABASE INITIALIZATION & STRUCTURE DEFINITION
# ==============================================================================
def setup_database() -> sqlite3.Connection:
    """
    Initializes the local SQLite database file, enforces foreign key 
    constraints, and sets up relational schemas for transactional logs.
    """
    conn = sqlite3.connect("triage_log.db")
    cursor = conn.cursor()
    
    # Strictly enforce relational integrity via Foreign Key Constraints
    cursor.execute("PRAGMA foreign_keys = ON;")
    # Optimize database memory handling metrics for active dashboard sync runs
    cursor.execute("PRAGMA journal_mode = WAL;")
    
    # Master Table: Primary structural application data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS application_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        service_name TEXT NOT NULL,
        log_level TEXT NOT NULL,
        message TEXT NOT NULL
    );
    """)
    
    # Slave Table: Highly granulized metadata traces linked directly to primary entries
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS log_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id INTEGER NOT NULL,
        http_status INTEGER,
        target_url TEXT,
        query_duration_seconds REAL,
        raw_sql TEXT,
        FOREIGN KEY (log_id) REFERENCES application_logs(id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    return conn


# ==============================================================================
# 03. RELATIONAL DATA PERSISTENCE ENGINE
# ==============================================================================
def save_to_database(conn: sqlite3.Connection, log_records: list) -> None:
    """
    Iterates through structured list inputs, committing entries safely to SQL.
    Ensures cascading logic captures auxiliary system metadata sequentially.
    """
    cursor = conn.cursor()
    
    for log in log_records:
        # Step A: Persist base record into master log stream
        cursor.execute("""
            INSERT INTO application_logs (timestamp, service_name, log_level, message)
            VALUES (?, ?, ?, ?);
        """, (log["timestamp"], log["service_name"], log["log_level"], log["message"]))
        
        # Step B: Intercept the auto-generated tracking key (Primary Key)
        log_id = cursor.lastrowid
        
        # Step C: If underlying sub-metadata was extracted, bind it via Foreign Key
        if log["metadata"]:
            meta = log["metadata"]
            cursor.execute("""
                INSERT INTO log_metadata (log_id, http_status, target_url, query_duration_seconds, raw_sql)
                VALUES (?, ?, ?, ?, ?);
            """, (
                log_id, 
                meta.get("http_status"), 
                meta.get("target_url"), 
                meta.get("query_duration_seconds"), 
                meta.get("raw_sql")
            ))
            
    conn.commit()


# ==============================================================================
# 04. SMART ALERTS ROUTER & INCIDENT DISPATCHER
# ==============================================================================
def run_alert_router(conn: sqlite3.Connection) -> None:
    """
    Queries the database clusters for high-severity risks, aggregates 
    duplicate events to suppress alert noise, and prints a structured 
    outbound JSON webhook payload ready for Slack/PagerDuty.
    """
    print("\n--- Running Incident Alert Dispatcher Engine ---")
    cursor = conn.cursor()
    
    # Consolidate duplicate incidents using advanced SQL GROUP BY aggregations
    cursor.execute("""
        SELECT log_level, service_name, message, COUNT(*) as occurrence_count
        FROM application_logs
        WHERE log_level IN ('ERROR', 'CRITICAL')
        GROUP BY log_level, service_name, message;
    """)
    
    incidents = cursor.fetchall()
    
    if not incidents:
        print("✅ No high-severity incidents flagged. Infrastructure healthy.")
        return

    # Build the standardized outbound alert wrapper schema
    alert_payload = {
        "alert_status": "TRIGGERED",
        "total_unique_incidents": len(incidents),
        "incidents": []
    }
    
    for row in incidents:
        severity = row[0]
        alert_payload["incidents"].append({
            "severity": severity,
            "impacted_service": row[1],
            "error_summary": row[2],
            "total_occurrences_suppressed": row[3],
            # Apply custom business logic SLAs conditionally based on risk vectors
            "action_required": (
                "Immediate Developer Investigation Needed" 
                if severity == "CRITICAL" 
                else "Triage via Next Release Window"
            )
        })
        
    # Serialize structured data objects seamlessly into minified JSON output streams
    print("🚨 [OUTBOUND ALERT PAYLOAD GENERATED] 🚨")
    print(json.dumps(alert_payload, indent=2))


# ==============================================================================
# 05. MASTER EXECUTION PIPELINE ENTRY
# ==============================================================================
def run_pipeline(file_path: str) -> None:
    """
    Main execution pipeline interface. Orchestrates log extraction, text cleaning,
    database schema building, persistence runs, and alert notifications from A-Z.
    """
    print(f"--- Launching Ingestion Engine Pipeline: {file_path} ---")
    log_records = []
    
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line: 
                continue
                
            # Perform granular string-matching evaluations
            match = re.match(LOG_PATTERN, line)
            if match:
                data = match.groupdict()
                
                # Standardize microsecond logging differences (e.g., commas vs periods)
                clean_timestamp = data['timestamp'].replace(',', '.')
                extra_metadata = extract_metadata(data['message'])
                
                # Sanitize text payloads cleanly away from composite metadata suffixes
                clean_message = data['message'].split(" | ")[0]
                
                log_records.append({
                    "timestamp": clean_timestamp,
                    "service_name": data['service'],
                    "log_level": data['level'],
                    "message": clean_message,
                    "metadata": extra_metadata if extra_metadata else None
                })
                
    # Initialize the local transactional environment
    db_conn = setup_database()
    
    # Persist records cleanly to active tables
    save_to_database(db_conn, log_records)
    
    # Assess infrastructure health logs for outbound escalation
    run_alert_router(db_conn)
    
    # Terminate the database session clean to free system threads
    db_conn.close()


if __name__ == "__main__":
    run_pipeline("production_logs.txt")