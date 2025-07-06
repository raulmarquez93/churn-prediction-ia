# file: $AIRFLOW_HOME/dags/api_to_kafka_split.py

from datetime import datetime, timedelta
import json
import requests
from kafka import KafkaProducer

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_data(**context):
    """
    1) Llama al endpoint y guarda el JSON en XCom bajo la clave 'payload'.
    """
    url = 'http://host.docker.internal:82/dato'
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    # Push al XCom
    context['ti'].xcom_push(key='payload', value=payload)

def send_to_kafka(**context):
    """
    2) Extrae el JSON de XCom y lo publica en Kafka.
    """
    # Pull desde XCom (task_id='extract_data')
    payload = context['ti'].xcom_pull(key='payload', task_ids='extract_data')
    if not payload:
        raise ValueError("No se encontró payload en XCom")

    producer = KafkaProducer(
        bootstrap_servers=['broker:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k is not None else None
    )

    producer.send('clientes-dato', value=payload)
    producer.flush()
    producer.close()

with DAG(
    dag_id='api_to_kafka_split',
    default_args=default_args,
    description='Extrae datos de la API y los publica en Kafka (2 tareas)',
    start_date=datetime(2025, 5, 1),
    schedule_interval=timedelta(minutes=1),
    catchup=False,
    tags=['streaming','kafka'],
) as dag:

    task_extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        provide_context=True,
    )

    task_send = PythonOperator(
        task_id='send_to_kafka',
        python_callable=send_to_kafka,
        provide_context=True,
    )

    # Define dependencia: primero extrae, luego envía
    task_extract >> task_send
