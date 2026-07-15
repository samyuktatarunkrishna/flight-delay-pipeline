"""
Apache Airflow DAG to orchestrate the Flight Delay and Traffic Pattern Analytics Pipeline.
This schedules and runs the pipeline tasks daily.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# Default arguments for DAG
default_args = {
    "owner": "data_engineering_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Define DAG
with DAG(
    "flight_delay_analytics_pipeline",
    default_args=default_args,
    description="End-to-end Flight Delay and Traffic volume pipeline",
    schedule_interval="@daily",
    catchup=False,
    tags=["aviation", "etl", "dbt", "spark"],
) as dag:

    # 1. Ingestion Task (Simulating Airbyte Sync)
    # In a real environment, this might trigger an Airbyte connection sync via AirbyteTriggerSyncOperator
    def run_ingestion_sync():
        print("Triggering Airbyte connection sync for flights_raw...")
        # Simulating data ingestion script
        from src.ingest_sim import generate_flight_data
        generate_flight_data(num_records=100000, output_path="data/raw/flights_raw.csv")

    ingest_task = PythonOperator(
        task_id="airbyte_ingestion_sync",
        python_callable=run_ingestion_sync,
    )

    # 2. PySpark Cleaning & Loading Task
    # Runs the PySpark script on a cluster to load the raw data into BigQuery
    spark_transform_task = SparkSubmitOperator(
        task_id="pyspark_warehouse_transform",
        application="src/spark_transform.py",
        name="pyspark_flight_transform",
        conn_id="spark_default",
        verbose=True,
        conf={
            "spark.yarn.submit.waitAppCompletion": "true",
            "spark.datasource.bigquery.temporaryGcsBucket": "aviation-pipeline-temp-bucket"
        }
    )

    # 3. dbt Model Transformations
    # Executes SQL compilation and physical table builds in BigQuery/Warehouse
    dbt_run_task = BashOperator(
        task_id="dbt_run_transformations",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir .",
    )

    # 4. dbt Data Quality Assertions
    # Runs schema and validation assertions against the newly generated marts
    dbt_test_task = BashOperator(
        task_id="dbt_test_assertions",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir .",
    )

    # Define orchestration flow
    ingest_task >> spark_transform_task >> dbt_run_task >> dbt_test_task
