import os
import sys
import subprocess
import time

# Add src to python path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_aviationstack import main as run_ingestion
from spark_transform_local import run_local_transform
from export_tableau import export_to_tableau

def run_pipeline():
    start_time = time.time()
    print("=" * 60)
    print("STARTING AVIATIONSTACK & TABLEAU ANALYTICS PIPELINE")
    print("=" * 60)

    # 1. Ingest Data (Aviationstack API or cache)
    raw_json_path = "data/raw/flights_aviationstack.json"
    db_path = "data/aviation_dw.db"
    
    print("\n--- STEP 1: Ingesting Aviationstack API Data ---")
    run_ingestion()

    # 2. Local Transform (PySpark simulation)
    print("\n--- STEP 2: Running ETL & DuckDB Load (PySpark emulation) ---")
    run_local_transform(input_json=raw_json_path, db_path=db_path)

    # Determine dbt executable path
    venv_dbt = os.path.join("venv", "bin", "dbt")
    dbt_exec = venv_dbt if os.path.exists(venv_dbt) else "dbt"
    
    project_dir = "dbt_project"
    profiles_dir = "dbt_project"

    # 3. Compile dbt seeds (Loads airports reference CSV into warehouse)
    print("\n--- STEP 3: Compiling Static Reference Data (dbt seed) ---")
    dbt_seed_cmd = [dbt_exec, "seed", "--project-dir", project_dir, "--profiles-dir", profiles_dir]
    print(f"Executing: {' '.join(dbt_seed_cmd)}")
    
    seed_result = subprocess.run(dbt_seed_cmd, capture_output=False)
    if seed_result.returncode != 0:
        print("ERROR: dbt seed loading failed. Exiting pipeline.")
        sys.exit(seed_result.returncode)
    print("dbt seeds compiled successfully.")

    # 4. Run dbt transformation models
    print("\n--- STEP 4: Running dbt Transformation Models ---")
    dbt_run_cmd = [dbt_exec, "run", "--project-dir", project_dir, "--profiles-dir", profiles_dir]
    print(f"Executing: {' '.join(dbt_run_cmd)}")
    
    run_result = subprocess.run(dbt_run_cmd, capture_output=False)
    if run_result.returncode != 0:
        print("ERROR: dbt run failed. Exiting pipeline.")
        sys.exit(run_result.returncode)
    print("dbt models compiled and run successfully.")

    # 5. Run dbt data quality tests
    print("\n--- STEP 5: Running dbt Data Quality Tests ---")
    dbt_test_cmd = [dbt_exec, "test", "--project-dir", project_dir, "--profiles-dir", profiles_dir]
    print(f"Executing: {' '.join(dbt_test_cmd)}")
    
    test_result = subprocess.run(dbt_test_cmd, capture_output=False)
    if test_result.returncode != 0:
        print("WARNING: dbt test failures detected. Check logs.")
    else:
        print("All dbt data quality assertions passed.")

    # 6. Export data for Tableau
    print("\n--- STEP 6: Exporting Clean CSVs for Tableau Import ---")
    export_to_tableau()

    duration = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {duration:.2f} SECONDS")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
