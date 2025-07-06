def cargar_configuracion_modelo(**kwargs):
    """
    Carga la configuración del modelo desde la última versión registrada
    de 'modelo_produccion_optimo' en el Model Registry de MLflow.
    """
    import mlflow
    from mlflow.tracking import MlflowClient

    ti = kwargs['ti']

    # Configuración de conexión
    mlflow.set_tracking_uri("http://host.docker.internal:5000")
    MODELO_REGISTRADO = "compañia_telefonica_abandono"
    client = MlflowClient()

    # Obtener última versión registrada del modelo
    versions = client.get_latest_versions(MODELO_REGISTRADO)
    if not versions:
        raise ValueError(f"No hay versiones registradas del modelo '{MODELO_REGISTRADO}'")

    # Tomamos la versión más reciente
    ultima_version = sorted(versions, key=lambda v: int(v.version), reverse=True)[0]
    run_id = ultima_version.run_id
    run = client.get_run(run_id)
    params = run.data.params

    # Utilidad para convertir parámetros desde string
    def parse_param(key, default=None, cast_type=str):
        value = params.get(key, default)
        if value is None:
            raise KeyError(f"Falta el parámetro '{key}' en el modelo (run_id: {run_id})")
        try:
            return cast_type(value)
        except Exception as e:
            raise ValueError(f"Error al convertir '{key}' a {cast_type}: {e}")

    # Construir diccionario de configuración
    conf = {
        "clientes_path": parse_param("conf_clientes_path", str),
        "servicios_path": parse_param("conf_servicios_path", str),
        "metodo_limpieza": parse_param("conf_metodo_limpieza", str),
        "usar_kbest": parse_param("conf_usar_kbest", str).lower() == "true",
        "k": parse_param("conf_k", int),
        "metodo_escalado": parse_param("conf_metodo_escalado", str),
        "validacion_cruzada": parse_param("conf_validacion_cruzada", str).lower() == "true",
        "modelo_fijo": parse_param("conf_modelo_fijo", str),
        "run_id_modelo": run_id,
    }

    print(f"✅ Configuración cargada desde la versión {ultima_version.version} del modelo:")
    for k, v in conf.items():
        print(f"  - {k}: {v}")

    # Guardar en XCom
    ti.xcom_push(key='configuracion_modelo', value=conf)
    ti.xcom_push(key='run_id_modelo', value=run_id)
    ti.xcom_push(key='version_modelo', value=ultima_version.version)
    ti.xcom_push(key='nombre_modelo', value=MODELO_REGISTRADO)
