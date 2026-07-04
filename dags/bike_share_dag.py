from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default settings for our pipeline
default_args = {
    'owner': 'data_engineer',
    'retries': 1,
    'retry_delay': timedelta(minutes=2), # Reverted back to 2 min
}

# Define the DAG
with DAG(
    'bike_share_etl',
    default_args=default_args,
    description='Extract, Transform, Load Bike Share Data',
    schedule_interval='*/5 * * * *', # Data collection every 5 minutes
    start_date=datetime(2026, 1, 1),
    catchup=False,
) as dag:

    # Task 1: Run the ingestion script
    run_ingestion = BashOperator(
        task_id='ingest_raw_data',
        bash_command='python /opt/airflow/scripts/ingest.py',
    )

    # Task 2: Run the transformation script
    run_transformation = BashOperator(
        task_id='transform_clean_data',
        bash_command='python /opt/airflow/scripts/transform.py',
    )

    # Define the dependency (Task 1 must finish before Task 2 starts)
    run_ingestion >> run_transformation