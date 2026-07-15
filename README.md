# Flight Delay and Traffic Pattern Analytics Pipeline

### 🌐 Live Telemetry Dashboard Preview
👉 **[Open the Live Interactive HUD Dashboard](https://samyuktatarunkrishna.github.io/flight-delay-pipeline/)** *(Compiled with offline-simulated fallback telemetry for recruiter preview: explore region filters, dynamic ATC radar map sweeps, and chart toggling directly in your browser!)*

An end-to-end data engineering pipeline designed to process and analyze over 100,000+ (configurable to 1M+) aviation records. This project highlights delay causes, traffic congestion patterns, and route-level flight performance using a modern data stack.

## Architecture & Technology Stack

The pipeline mirrors a real-world enterprise cloud architecture, while providing a fully functional local emulation layer for rapid local testing on your Mac:

```
[ Ingestion (Airbyte) ] ──> Raw CSV ──> [ ETL & Cleaning (PySpark) ] ──> Local DW (DuckDB)
                                                                               │
                                                                               ▼
[ Interactive Dashboard ] <── [ API (FastAPI) ] <── [ Analytics Marts ] <── [ dbt Core ]
```

- **Source Ingestion (Airbyte)**: Simulated by a high-fidelity python script (`ingest_sim.py`) that outputs structured flight logs with authentic distributions of delay factors, airlines, and airport hubs.
- **Big Data Processing (PySpark & BigQuery)**: Includes a production-grade PySpark ETL script (`spark_transform.py`) suitable for GCP Dataproc or AWS EMR. For local execution, a Pandas/DuckDB script (`spark_transform_local.py`) runs the exact same validation and loading logic.
- **Data Warehouse (BigQuery / DuckDB)**: DuckDB acts as the local analytical database (`data/aviation_dw.db`), offering blazingly fast SQL analytics.
- **Data Transformations (dbt)**: Configured with `dbt-duckdb` to run staging models and materialize analytics marts:
  - `fct_delays`: Breakdowns of carrier, weather, NAS, security, and late-aircraft delays.
  - `mart_route_performance`: Volume, avg delays, and on-time percentages per route.
  - `mart_congestion`: Peak congestion and delay rate trends by hour and day of the week.
- **Orchestration (Airflow)**: An Apache Airflow DAG file (`flight_pipeline_dag.py`) is provided for automated scheduling. A lightweight local python orchestrator (`orchestrator.py`) automates execution locally.
- **Visualization (Tableau / Custom Dashboard)**: A premium glassmorphic dark-mode web application built with a FastAPI backend and a custom Vanilla CSS + Chart.js client frontend.

---

## Getting Started

### 1. Installation

Set up the virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Ingestion & Transformation Pipeline
You can trigger the entire pipeline (data generation, local transformation, and dbt compiles/tests) with a single command:
```bash
python3 src/orchestrator.py
```
This script will:
1. Synthesize 100,000 flight log records into `data/raw/flights_raw.csv`.
2. Process and load them into `data/aviation_dw.db` as the `raw_flights` table.
3. Execute `dbt run` to compile staging views and physical analytics marts.
4. Execute `dbt test` to validate schema integrity and data quality constraints.

*Note: You can configure the number of generated records by running: `python3 src/ingest_sim.py --records 1000000`*

### 3. Launch the Analytics Dashboard
Launch the FastAPI backend server and automatically open the user interface in your web browser:
```bash
python3 dashboard/run_dashboard.py
```
Open your browser to `http://localhost:8000` if it doesn't open automatically.

---

## Project Structure

- `src/`
  - `ingest_sim.py`: Synthesizes mock raw aviation data.
  - `spark_transform.py`: Production PySpark script for Cloud / BigQuery pipelines.
  - `spark_transform_local.py`: Local transformation script querying DuckDB.
  - `orchestrator.py`: Sequence coordinator executing pipeline jobs.
  - `api.py`: FastAPI server querying data and hosting routes.
- `dbt_project/`
  - `dbt_project.yml` / `profiles.yml`: Project configurations.
  - `models/staging/`: Staging model and test schema.
  - `models/marts/`: Fact and analytics models (delays, congestion, routes).
- `airflow/dags/`
  - `flight_pipeline_dag.py`: Orchestrator scheduling script.
- `dashboard/`
  - `templates/index.html`: Dashboard structure.
  - `static/css/style.css`: Glassmorphism design styling.
  - `static/js/app.js`: Chart rendering and fetch controllers.
  - `run_dashboard.py`: Dashboard launcher.
