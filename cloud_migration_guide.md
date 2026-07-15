# Cloud Warehouse Migration Guide: Migrating to GCP BigQuery or AWS Redshift

This guide outlines how to transition the flight delay pipeline from local emulation (**DuckDB**) to a production **Cloud Data Warehouse** on **Google Cloud BigQuery** or **AWS Redshift** using dbt adapters and PySpark.

---

## 1. Google Cloud BigQuery (Recommended)

Google Cloud BigQuery is a serverless, highly scalable DW. Moving the pipeline here requires changing your dbt adapter and updating connection profiles.

### Step A: Install the BigQuery dbt Adapter
Run the following in your virtual environment:
```bash
pip install dbt-bigquery
```

### Step B: Configure GCP Service Account Credentials
1. In your GCP Console, navigate to **IAM & Admin** -> **Service Accounts**.
2. Create a service account with the role **BigQuery Admin**.
3. Generate a new **JSON private key** and save it locally (e.g., `~/.gcp/bigquery-key.json`).

### Step C: Update `profiles.yml` for BigQuery
Replace your `dbt_project/profiles.yml` with the following configuration:

```yaml
flight_delay_analytics:
  outputs:
    dev:
      type: bigquery
      method: service-account
      project: your-gcp-project-id  # Replace with your GCP project ID
      dataset: flight_delay_analytics  # The BigQuery dataset to create tables in
      threads: 4
      keyfile: /Users/samyuktareddy/.gcp/bigquery-key.json  # Path to your JSON key
      timeout_seconds: 300
      priority: interactive
      retries: 1
  target: dev
```

### Step D: Update PySpark ETL to Load BigQuery
In `src/spark_transform.py`, PySpark uses the GCS temporary bucket bucket to stage and write directly to BigQuery tables:
```python
df.write \
  .format("bigquery") \
  .option("temporaryGcsBucket", "your-gcs-temp-bucket") \
  .option("table", "your-gcp-project-id.flight_delay_analytics.raw_flights") \
  .mode("overwrite") \
  .save()
```

---

## 2. AWS Redshift

AWS Redshift is a fully managed, petabyte-scale data warehouse. To deploy the pipeline on AWS, configure the Redshift adapter.

### Step A: Install the Redshift dbt Adapter
Run the following in your virtual environment:
```bash
pip install dbt-redshift
```

### Step B: Update `profiles.yml` for Redshift
Replace your `dbt_project/profiles.yml` with this target definition:

```yaml
flight_delay_analytics:
  outputs:
    dev:
      type: redshift
      host: your-redshift-cluster.xxxxx.us-east-1.redshift.amazonaws.com
      port: 5439
      user: your_redshift_user
      password: your_redshift_password
      dbname: dev
      schema: flight_delay_analytics
      threads: 4
      keepalives_idle: 240 # Prevents connection drops on long compilations
  target: dev
```

### Step C: Update PySpark ETL to load AWS S3 & Redshift
In your Spark script, write the cleaned dataframe to an AWS S3 bucket as parquet files, and run a COPY command to load it into Redshift:
```python
# Save clean records to S3 staging
df.write.parquet("s3a://your-staging-bucket/clean-flights/", mode="overwrite")

# Trigger COPY command on Redshift connection
con.execute("""
    COPY flight_delay_analytics.raw_flights 
    FROM 's3://your-staging-bucket/clean-flights/' 
    IAM_ROLE 'arn:aws:iam::xxxxxxx:role/RedshiftS3LoadRole'
    FORMAT AS PARQUET;
""")
```

---

## 3. Running dbt on the Cloud

Once your `profiles.yml` is updated to point to BigQuery or Redshift:
1. Initialize the seed tables in your cloud database:
   ```bash
   dbt seed
   ```
2. Compile and materialize all view models and marts in your cloud database:
   ```bash
   dbt run
   ```
3. Run data quality assertion checks on BigQuery/Redshift:
   ```bash
   dbt test
   ```

*Because dbt compiles SQL code dynamically, all models (`fct_delays`, `mart_congestion`, `mart_route_performance`) will automatically translate and execute in BigQuery Standard SQL or Redshift PG-SQL dialects without requiring any changes to your SQL code!*
