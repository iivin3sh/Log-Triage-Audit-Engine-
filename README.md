# Enterprise Observability Pipeline and Automated SQL Audit Engine

https://fsxcrdo7qcv2ufbgwmhvkx.streamlit.app/

## 1. System Overview
This project implements a high-performance, memory-efficient asynchronous log triaging pipeline. The system processes unstructured, high-velocity application log buffers, normalizes composite text strings into structured relational data objects, and performs continuous database auditing to detect query latency anomalies and suppress redundant system alerts

## 2. Architecture and Data Lifecycle
The application functions as a unidirectional Data Engineering pipeline following strict ETL (Extract, Transform, Load) protocols:

* **Ingestion (Extract):** Reads inbound streaming log files sequentially using line-by-line file handlers to maintain an $O(1)$ flat memory footprint, preventing heap exhaustion during multi-gigabyte processing runs.
* **Normalization (Transform):** Utilizes a structured regular expression matrix to isolate foundational variables (timestamps, calling services, and severity levels) while parsing auxiliary metadata payloads (HTTP codes, network paths, and raw execution traces).
* **Persistence (Load):** Ingests sanitized records into decoupled relational database layers leveraging ACID-compliant transactional grouping and Write-Ahead Logging (WAL) engine configurations.
* **Analysis (Audit & Alert):** Runs automated analytical queries over relational indexes to cluster identical service anomalies, calculate outage rates, and profile query bottlenecks.

## 3. Core Software Engineering Concepts Demonstrated
* **Relational Database Design:** Normalization of high-throughput write streams across primary (`application_logs`) and secondary (`log_metadata`) structural tables utilizing Foreign Key constraints and cascading deletes.
* **Database Performance Tuning:** Implementing Write-Ahead Logging (WAL) state optimization to allow concurrent read/write locks, preventing ingestion thread blockages during live analytical operations.
* **Memory Optimization:** Streaming file system I/O handling via native iteration blocks rather than full-file memory mapping blocks to preserve hardware constraints under heavy production workloads.
* **Deterministic String Parsing:** Using captured regex groups to tokenize arbitrary, variant string suffixes dynamically into strongly-typed object mappings.

## 4. File Structure
* `parser.py`: Core pipeline engine containing the regular expression patterns, metadata parsers, relational database initialization routines, and the JSON alert aggregation module.
* `app.py`: Analytics and operational interface displaying high-level system metrics, dynamic relational table filters, and execution latency tracing.
* `chaos_generator.py`: Mock system simulation script appending varying error states and database delays to mock a standard production load.
* `production_logs.txt`: Unstructured base data dump detailing standard microservice operational outcomes.

## 5. Execution Instructions

### Prerequisites
Ensure dependency binaries are installed locally via package management utilities:
```bash
pip install streamlit pandas
