def predecir_modelo(**kwargs):
    import pandas as pd
    import requests
    import os
    from mlflow.tracking import MlflowClient

    ti = kwargs['ti']

    # 1) Cargar los datos procesados
    input_path = '/opt/airflow/dags/data/datos_unificados.csv'
    if not os.path.exists(input_path):
        raise FileNotFoundError("El archivo de datos unificados no existe.")
    df = pd.read_csv(input_path)
    if 'abandono' in df.columns:
        df = df.drop(columns=['abandono'])

    records = df.to_dict(orient='records')

    # 2) Llamar a FastAPI
    url = "http://host.docker.internal:8000/predict"
    response = requests.post(url, json=records)
    response.raise_for_status()
    predictions = response.json().get("predictions", [])
    print(f"Predicciones recibidas: {len(predictions)} registros procesados.")

    # 3) Empujar a XCom
    ti.xcom_push(key='inputs',      value=records)
    ti.xcom_push(key='predictions', value=predictions)

    return predictions
