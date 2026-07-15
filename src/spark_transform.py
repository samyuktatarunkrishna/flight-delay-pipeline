"""
Production PySpark transformation job for the Flight Delay Analytics Pipeline.
This script runs in a cloud environment (e.g. AWS EMR, GCP Dataproc, Databricks)
to process large-scale raw data from Cloud Storage and load it into Google BigQuery.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, to_date, concat, lit, lpad, to_timestamp

def main():
    # 1. Initialize Spark Session with BigQuery connector support
    spark = SparkSession.builder \
        .appName("FlightDelayAnalyticsETL") \
        .config("viewsEnabled", "true") \
        .config("materializationDataset", "aviation_analytics_staging") \
        .getOrCreate()

    # 2. Read raw CSV ingestion output (e.g., from an S3 bucket or Google Cloud Storage)
    # In production, this path would point to gs://bucket-name/raw/flights_raw.csv
    raw_data_path = "data/raw/flights_raw.csv" 
    print(f"Reading raw flight data from {raw_data_path}...")
    
    df = spark.read.option("header", "true") \
                   .option("inferSchema", "true") \
                   .csv(raw_data_path)

    # 3. Clean and Transform Data
    print("Beginning Spark transformation schema transformations...")
    
    # - Fill null delay fields with 0 (since they represent no delay)
    delay_columns = [
        "carrier_delay", "weather_delay", "nas_delay", 
        "security_delay", "late_aircraft_delay"
    ]
    for col_name in delay_columns:
        df = df.withColumn(col_name, when(col(col_name).isNull(), 0).otherwise(col(col_name)))

    # - Handle cancelled and diverted fields, casting them properly to integers
    df = df.withColumn("cancelled", col("cancelled").cast("integer")) \
           .withColumn("diverted", col("diverted").cast("integer")) \
           .withColumn("flight_num", col("flight_num").cast("string"))

    # - Convert flight_date to DateType
    df = df.withColumn("flight_date", to_date(col("flight_date"), "yyyy-MM-dd"))

    # - Standardize dep_time and arr_time to 4-character strings (e.g., "0830" or "1445")
    #   and construct departure/arrival timestamps
    df = df.withColumn("dep_time_str", lpad(col("dep_time").cast("string"), 4, "0")) \
           .withColumn("arr_time_str", lpad(col("arr_time").cast("string"), 4, "0"))

    # - Create timestamps by joining flight_date and time strings
    #   Departure Timestamp
    df = df.withColumn("dep_timestamp_str", 
                       concat(col("flight_date").cast("string"), lit(" "), 
                              col("dep_time_str").substr(1, 2), lit(":"), 
                              col("dep_time_str").substr(3, 2), lit(":00"))) \
           .withColumn("dep_timestamp", to_timestamp(col("dep_timestamp_str")))

    #   Arrival Timestamp
    df = df.withColumn("arr_timestamp_str", 
                       concat(col("flight_date").cast("string"), lit(" "), 
                              col("arr_time_str").substr(1, 2), lit(":"), 
                              col("arr_time_str").substr(3, 2), lit(":00"))) \
           .withColumn("arr_timestamp", to_timestamp(col("arr_timestamp_str")))

    # - Clean up helper columns
    processed_df = df.drop("dep_time_str", "arr_time_str", "dep_timestamp_str", "arr_timestamp_str")

    # 4. Write to BigQuery (or a staging warehouse)
    # The spark-bigquery-connector enables direct writing into BigQuery tables
    bq_dataset_table = "aviation_analytics.raw_flights"
    temporary_gcs_bucket = "aviation-pipeline-temp-bucket"
    
    print(f"Writing transformed data to BigQuery table: {bq_dataset_table}...")
    
    # In a production GCP/Dataproc pipeline, uncomment this block to load:
    """
    processed_df.write \
        .format("bigquery") \
        .option("table", bq_dataset_table) \
        .option("temporaryGcsBucket", temporary_gcs_bucket) \
        .mode("overwrite") \
        .save()
    """
    
    # For documentation and local validation, we save it as a parquet file:
    local_output_path = "data/processed/flights_processed"
    processed_df.write.mode("overwrite").parquet(local_output_path)
    
    print(f"Pipeline Spark Stage Completed successfully. Local Parquet saved to {local_output_path}")

if __name__ == "__main__":
    main()
