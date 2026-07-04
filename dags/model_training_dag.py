from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

# Define the DAG for Continuous Training
with DAG(
    'bike_share_model_training',
    description='Automated 15-Minute Machine Learning Model Retraining',
    schedule_interval='*/15 * * * *', # Train every 15 minutes
    start_date=datetime(2026, 7, 3),
    catchup=False,
) as dag:

    # Task: Run the training script from the mounted project folder
    retrain_model = BashOperator(
        task_id='retrain_random_forest',
        bash_command='python /opt/airflow/project/train_model.py',
    )