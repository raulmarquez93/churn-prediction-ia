# inference_modules/evaluar_modelo.py
def evaluar_modelo(**kwargs):
    import pandas as pd, requests, os

    ti = kwargs['ti']

    # 1) Cargar ground-truth desde el CSV de clientes
    data_path = '/opt/airflow/dags/data/clientes.csv'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Falta el fichero de ground-truth: {data_path}")
    df = pd.read_csv(data_path, sep=';')

    # Mapear Abandono a 0/1
    mapping = {'Yes': 1, 'No': 0, 'yes': 1, 'no': 0, '1': 1, '0': 0}
    df['Abandono'] = df['Abandono'].map(mapping)
    if df['Abandono'].isnull().any():
        bad = df.loc[df['Abandono'].isnull(), 'Abandono'].unique()
        raise ValueError(f"Valores inválidos en 'Abandono': {bad}")
    y_true = df['Abandono'].astype(int).tolist()

    # 2) Recuperar las predicciones del task predecir_modelo
    preds = ti.xcom_pull(task_ids='predecir_modelo', key='predictions')
    if preds is None:
        raise ValueError("No se encontraron predicciones en XCom de predecir_modelo")

    # 3) Llamar al endpoint de evaluación
    url = "http://host.docker.internal:84/evaluate"
    payload = {"predictions": preds}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    result = resp.json()

    # 4) “Push” de las métricas a XCom para poder usarlas más tarde
    ti.xcom_push(key='roc_auc', value=result.get('roc_auc'))
    print(f"✅ Evaluación completada: ROC-AUC = {result.get('roc_auc'):.4f}")

    return result
