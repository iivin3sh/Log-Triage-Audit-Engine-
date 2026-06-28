import sqlite3
import pandas as pd
import streamlit as st
import os

# ==============================================================================
# 00. INITIALIZATION & LOG PIPELINE RUNNERS
# ==============================================================================

# CORE AUTOMATION: If the application starts up and finds no historical database,
# it automatically targets the default log file to initialize the entire environment.
DEFAULT_LOGS = "production_logs.txt"
from parser import run_pipeline

if not os.path.exists("triage_log.db") and os.path.exists(DEFAULT_LOGS):
    try:
        run_pipeline(DEFAULT_LOGS)
    except Exception:
        pass

# ==============================================================================
# 01. GLOBAL PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Log Triage Dashboard", 
    page_icon="📊", 
    layout="wide"
)

st.title("📊 AI-Driven Log Triage & SQL Audit Dashboard")
st.markdown("Transforming unstructured server chaos into clean, actionable infrastructure metrics.")


# ==============================================================================
# 02. DATABASE CONNECTION & CORE UTILITIES
# ==============================================================================
DB_FILE = "triage_log.db"

def get_db_connection():
    """
    Establishes and returns a connection to the local SQLite database.
    Utilized within context managers to ensure strict connection hygiene.
    """
    return sqlite3.connect(DB_FILE)


# ==============================================================================
# 03. SIDEBAR CONTROLS & LOG INGESTION
# ==============================================================================
st.sidebar.header("🔍 Control Center")
st.sidebar.subheader("📥 Upload New Server Logs")

# Accept asynchronous log file uploads from users
uploaded_file = st.sidebar.file_uploader("Choose a text log file", type=["txt", "log"])

if uploaded_file is not None:
    # Decode binary file stream to standard UTF-8 string format
    log_contents = uploaded_file.read().decode("utf-8")
    
    # Temporarily persist the stream to disk to allow the parser module to ingest it
    with open("temp_production_logs.txt", "w", encoding="utf-8") as f:
        f.write(log_contents)
        
    # Trigger the backend parsing and AI pipeline execution engine
    run_pipeline("temp_production_logs.txt")
    st.sidebar.success("🚀 Logs processed and injected into SQL!")
    st.rerun()

# ADMINISTRATIVE FEATURE: Clear Database Engine Slate
st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Database Administration")
if st.sidebar.button("🗑️ Reset Database System"):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE) # Deletes the physical database file completely
    st.sidebar.warning("Database cleared completely!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtering Options")

# Populate the Service Filter dropdown dynamically from active database records
try:
    with get_db_connection() as conn:
        services_df = pd.read_sql("SELECT DISTINCT service_name FROM application_logs", conn)
    services_list = ["All Services"] + services_df["service_name"].tolist()
    selected_service = st.sidebar.selectbox("Filter by Service Focus", services_list)
except Exception:
    # Fallback default configuration if the database or table hasn't been initialized yet
    selected_service = "All Services"


# ==============================================================================
# 04. HIGH-LEVEL INFRASTRUCTURE KPI METRICS
# ==============================================================================
st.subheader("📈 High-Level Infrastructure Status")
col1, col2, col3 = st.columns(3)

try:
    with get_db_connection() as conn:
        # Run analytical counting aggregates over transactional tables
        total_logs = pd.read_sql("SELECT COUNT(*) FROM application_logs", conn).iloc[0, 0]
        critical_errors = pd.read_sql(
            "SELECT COUNT(*) FROM application_logs WHERE log_level IN ('ERROR', 'CRITICAL')", 
            conn
        ).iloc[0, 0]
        slow_queries = pd.read_sql(
            "SELECT COUNT(*) FROM log_metadata WHERE query_duration_seconds > 1.0", 
            conn
        ).iloc[0, 0]
except Exception:
    # Clean zeros fallback to keep the layout from breaking on zero-state initializations
    total_logs, critical_errors, slow_queries = 0, 0, 0

# Render standard metric cards onto the layout rows
with col1:
    st.metric(label="Total Log Records Ingested", value=total_logs)

with col2:
    # Dynamic alert flags that shift states based on current severity metrics
    is_critical = critical_errors > 0
    st.metric(
        label="High-Severity Incidents Triage", 
        value=critical_errors, 
        delta="Action Required" if is_critical else "System Safe", 
        delta_color="inverse" if is_critical else "normal"
    )

with col3:
    st.metric(label="Slow SQL Queries Tracked", value=slow_queries)

st.markdown("---")


# ==============================================================================
# 05. LIVE INGESTED LOG DATA STREAM & SEVERITY MAPPING
# ==============================================================================
st.subheader("📂 Ingested Live Log Stream")

# Build data stream query conditionally based on current sidebar inputs
log_query = "SELECT id, timestamp, service_name, log_level, message FROM application_logs"
if selected_service != "All Services":
    log_query += f" WHERE service_name = '{selected_service}'"
log_query += " ORDER BY id DESC"

try:
    with get_db_connection() as conn:
        df_logs = pd.read_sql(log_query, conn)
except Exception:
    df_logs = pd.DataFrame()

def color_severity(val):
    """
    Dataframe styling mapper function. Maps explicit CSS injections 
    to specific logging severity strings to guide user attention.
    """
    if val == "CRITICAL": 
        return "background-color: #ff4b4b; color: white; font-weight: bold;"
    if val == "ERROR": 
        return "background-color: #ffa500; color: black; font-weight: bold;"
    if val == "WARN": 
        return "background-color: #ffee99; color: black;"
    return ""

# Render styled data stream matrix onto main stage
if not df_logs.empty:
    st.dataframe(
        df_logs.style.map(color_severity, subset=['log_level']), 
        use_container_width=True
    )
else:
    st.info("No active log streams discovered in storage. Please upload a file or launch the generator script.")


# ==============================================================================
# 06. BACKEND DATABASE PERFORMANCE METRICS AUDIT
# ==============================================================================
st.subheader("⚠️ Database Engine Performance Audit")

# Relational join query mapping structural processing times against application layers
audit_query = """
    SELECT al.service_name, lm.query_duration_seconds, lm.raw_sql 
    FROM application_logs al
    JOIN log_metadata lm ON al.id = lm.log_id
    WHERE lm.query_duration_seconds IS NOT NULL
    ORDER BY lm.query_duration_seconds DESC
"""

try:
    with get_db_connection() as conn:
        df_audit = pd.read_sql(audit_query, conn)
except Exception:
    df_audit = pd.DataFrame()

# Highlight or clear the internal operational layer performance threshold
if not df_audit.empty:
    st.warning("Database parser layers detected active structural delays. Slowest query trace:")
    st.table(df_audit)
else:
    st.success("Database query layers operating efficiently within target threshold limits (< 1.0s).")