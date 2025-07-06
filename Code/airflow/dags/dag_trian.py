from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os 
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from modules.cargadatos import cargar_datos_clientes, cargar_datos_servicios
from modules.transformaciones import transformar_datos_clientes, transformar_datos_servicios, transformacion_final
from modules.train import entrenar_modelo
from modules.eval import evaluar_modelo
from modules.register import registrar_modelo_en_mlflow
from modules.seleccion_modelo import seleccion_modelo

with DAG("entrenamiento",
         start_date=datetime(2023, 1, 1),
         schedule_interval=None,
         max_active_runs=1,   
         concurrency=1,
         catchup=False) as dag:

    recibir_datos_clientes = PythonOperator(
        task_id="cargar_datos_clientes",
        python_callable=cargar_datos_clientes,
        provide_context=True
    )
    recibir_datos_servicios = PythonOperator(
        task_id="cargar_datos_servicios",
        python_callable=cargar_datos_servicios,
        provide_context=True
    )
    transformar_clientes = PythonOperator(
        task_id="transformar_datos_clientes",
        python_callable=transformar_datos_clientes,
        provide_context=True
    )

    transformar_servicios = PythonOperator(
        task_id="transformar_datos_servicios",
        python_callable=transformar_datos_servicios,
        provide_context=True
    )
    transform_final = PythonOperator(
        task_id="transformacion_final",
        python_callable=transformacion_final,
        provide_context=True
    )
    train_task = PythonOperator(
        task_id="entrenar_modelo",
        python_callable=entrenar_modelo,
        do_xcom_push=False
    )

    eval_task = PythonOperator(
        task_id="evaluar_modelo",
        python_callable=evaluar_modelo
    )
    registrar = PythonOperator(
        task_id="registrar_modelo",
        python_callable=registrar_modelo_en_mlflow
    )
    seleccionar = PythonOperator(
        task_id="seleccion_modelo",
        python_callable=seleccion_modelo
    )

    
recibir_datos_clientes >> transformar_clientes >> transform_final
recibir_datos_servicios >> transformar_servicios >> transform_final
transform_final >> train_task >> eval_task >> registrar >> seleccionar
