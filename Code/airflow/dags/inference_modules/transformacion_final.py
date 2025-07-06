def transformacion_final(**kwargs):
    import os
    import pickle
    import pandas as pd
    import mlflow

    from modules.transformaciones import unificar_datos
    from mlflow.tracking import MlflowClient

    ti = kwargs['ti']
    conf = ti.xcom_pull(task_ids='cargar_configuracion_modelo', key='configuracion_modelo')
    run_id = conf.get("run_id_modelo")  # extraerlo desde el diccionario

    if not run_id or not isinstance(run_id, str):
        raise ValueError(f"❌ run_id no válido recibido desde XCom: {run_id}")
    usar_kbest = conf.get("usar_kbest", False)
    k = int(conf.get("k", 10))  # no se usa aquí, pero por si acaso

    df_clientes = ti.xcom_pull(task_ids='transformar_datos_clientes', key='clientes_limpios')
    df_servicios = ti.xcom_pull(task_ids='transformar_datos_servicios', key='servicios_limpios')

    if df_clientes is None or df_servicios is None:
        raise ValueError("No se encontraron datos en XCom (clientes o servicios)")

    df = unificar_datos(df_clientes, df_servicios)
    print("📦 Datos unificados:", df.shape)
    print(df.columns)

    # Conexión MLflow
    mlflow.set_tracking_uri("http://host.docker.internal:5000")
    client = MlflowClient()

    # 🔽 Descargar artefactos
    descarga_dir = "/opt/airflow/dags/data"
    
    print("⬇️ Descargando columnas...")
    columnas_path = client.download_artifacts(run_id, "columnas/columnas_entrenamiento.txt", descarga_dir)

    print("⬇️ Descargando scaler...")
    scaler_path = client.download_artifacts(run_id, "scaler/scaler.pkl", descarga_dir)



    print("⬇️ Descargando encoders...")
    labelenc_path = client.download_artifacts(run_id, "label_encoders/label_encoders.pkl", descarga_dir)

    
    kbest_path = None
    try:
        kbest_path = client.download_artifacts(run_id, "kbest/kbest_columnas.txt", descarga_dir)
    except Exception:
        print("ℹ️ No se encontró KBest, se usará todo el dataset.")

    # 🔁 Codificación
    with open(labelenc_path, "rb") as f:
        label_encoders = pickle.load(f)
    for col, le in label_encoders.items():
        if col in df.columns:
            df[col] = le.transform(df[col].astype(str))
        else:
            raise ValueError(f"❌ Columna '{col}' no encontrada en datos para codificar.")

    # 🔁 Escalado
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    # Asegurar orden de columnas
    with open(columnas_path, "r") as f:
        columnas = f.read().splitlines()
    df = df[columnas]

    df_scaled = pd.DataFrame(scaler.transform(df), columns=columnas)

    # 🔁 KBest si aplica
    if usar_kbest and kbest_path:
        with open(kbest_path, "r") as f:
            columnas_kbest = f.read().splitlines()
        df_scaled = df_scaled[columnas_kbest]

    # Guardar CSV final
    df_scaled_path = "/opt/airflow/dags/data/datos_unificados.csv"
    df_scaled.to_csv(df_scaled_path, index=False)

    ti.xcom_push(key='datos_finales', value=df_scaled)
    print(f"✅ Transformación completada para inferencia: {df_scaled.shape}")
