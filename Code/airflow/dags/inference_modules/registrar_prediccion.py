def guardar_predicciones_en_bd(**kwargs):
    """
    Tarea de Airflow para guardar en TimescaleDB las predicciones realizadas.
    Espera que la tarea 'predecir' haya empujado a XCom:
      - key='predictions': lista de valores predichos
      - key='inputs':      lista de dicts con los datos de entrada (opcional)
      - key='mlflow_run_id': ID de ejecución de MLflow
      - key='model_version': versión del modelo usado
    """
    from mlflow.tracking import MlflowClient
    from timescale.connector import TimescaleDBConnector, Model, Prediction  # Ajusta el import a tu estructura
    import logging
    import mlflow
    mlflow.set_tracking_uri("http://host.docker.internal:5000")

    # 1) Recuperar contexto y datos desde XCom
    ti = kwargs['ti']
    preds = ti.xcom_pull(task_ids='predecir_modelo', key='predictions')
    inputs = ti.xcom_pull(task_ids='predecir_modelo', key='inputs') or []
    run_id = ti.xcom_pull(task_ids='cargar_configuracion_modelo', key='run_id_modelo')
    model_version = ti.xcom_pull(task_ids='cargar_configuracion_modelo', key='version_modelo')
    model_name = ti.xcom_pull(task_ids='cargar_configuracion_modelo', key='nombre_modelo')

    # Validar que tenemos los datos necesarios
    logging.info(f"Guardando {len(preds)} predicciones en TimescaleDB para run_id={run_id}, model_version={model_version}")
    logging.info(f"inputs: {inputs[:5]}...")  # Muestra solo los primeros 5 inputs para no saturar el log
    if not preds or not run_id or not model_version:

        logging.error("Faltan datos en XCom para guardar predicciones.")
        return

    # 2) Conectar a TimescaleDB via SQLAlchemy
    connector = TimescaleDBConnector(
        host="timescaledb",
        port=5432,
        user="postgres",
        password="postgres",
        database="timescale"
    )
    session = connector.Session()

    # 3) Obtener o crear el registro del modelo
    model_obj = (
        session.query(Model)
        .filter_by(model_name=model_name, model_version=model_version)
        .first()
    )
    if not model_obj:
        client = MlflowClient()
        run = client.get_run(run_id)
        model_obj = Model(
            model_name=model_name,
            model_version=model_version,
            mlflow_run_id=run_id,
            parameters=run.data.params,
            metrics=run.data.metrics,
        )
        session.add(model_obj)
        session.commit()
        logging.info(f"Creado Model record id={model_obj.model_id}")

    # 4) Insertar cada predicción
    for inp, p in zip(inputs, preds):
        rec = Prediction(
            model_id=model_obj.model_id,
            input_data=inp,
            prediction_value=float(p)
        )
        session.add(rec)

    session.commit()
    logging.info(f"Guardadas {len(preds)} predicciones para model_id={model_obj.model_id}")
    session.close()
