from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os 
sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from modules.cargadatos import cargar_datos_clientes, cargar_datos_servicios
from modules.transformaciones import transformar_datos_clientes, transformar_datos_servicios, transformacion_final
from inference_modules.cargar_configuracion import cargar_configuracion_modelo
from inference_modules.transformacion_final import transformacion_final
from inference_modules.inferencia import predecir_modelo
from inference_modules.registrar_prediccion import guardar_predicciones_en_bd
from inference_modules.evaluar_modelo import evaluar_modelo

with DAG("inferencia",
         start_date=datetime(2023, 1, 1),
         schedule_interval=None,
         max_active_runs=2,   
         concurrency=2,
         catchup=False) as dag:
    cargar_configuracion = PythonOperator(
        task_id="cargar_configuracion_modelo",
        python_callable=cargar_configuracion_modelo,
        provide_context=True
    )
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
    predecir = PythonOperator(
        task_id="predecir_modelo",
        python_callable=predecir_modelo,
        provide_context=True
    )
    evaluar = PythonOperator(
        task_id="evaluar_modelo",
        python_callable=evaluar_modelo,
        provide_context=True,
    )
    guardar_predicciones = PythonOperator(
        task_id="guardar_predicciones_en_bd",
        python_callable=guardar_predicciones_en_bd,
        provide_context=True
    )

    

cargar_configuracion >> recibir_datos_clientes >> transformar_clientes >> transform_final
cargar_configuracion >> recibir_datos_servicios >> transformar_servicios >> transform_final
transform_final >> predecir 
predecir >> evaluar 
predecir >> guardar_predicciones