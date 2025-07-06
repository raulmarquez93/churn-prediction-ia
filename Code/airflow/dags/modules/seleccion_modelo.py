def seleccion_modelo(**kwargs):
    import mlflow
    from mlflow.tracking import MlflowClient
    import logging

    # Configuración
    mlflow.set_tracking_uri("http://host.docker.internal:5000")
    EXPERIMENT_NAME = "prediccion_abandono"
    MODELO_REGISTRADO = "prediccion_abandono"
    client = MlflowClient()
    logging.basicConfig(level=logging.INFO)

    def modelo_ya_registrado(nombre_modelo, run_id):
        versions = client.search_model_versions(f"name='{nombre_modelo}'")
        return any(v.run_id == run_id for v in versions)

    # 1) Obtener el experimento
    exp = client.get_experiment_by_name(EXPERIMENT_NAME)
    if exp is None:
        logging.error(f"No existe el experimento '{EXPERIMENT_NAME}'")
        return
    exp_id = exp.experiment_id

    # 2) Listar las últimas N corridas ordenadas por roc_auc
    runs = client.search_runs(
        experiment_ids=[exp_id],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["metrics.roc_auc DESC"],
        max_results=50  # Por si hay muchas corridas
    )
    if not runs:
        logging.warning(f"No hay corridas finalizadas en el experimento {EXPERIMENT_NAME}")
        return

    # 3) Buscar la mejor corrida que cumpla umbrales
    best_run = None
    best_score = -float("inf")
    for run in runs:
        m = run.data.metrics
        # Mostrar diagnósticos
        logging.debug(f"Run {run.info.run_id}: metrics={m}")

        # Verificamos que existan las métricas necesarias
        if not all(k in m for k in ("roc_auc", "train_auc", "f1_score")):
            continue

        roc_auc = m["roc_auc"]
        train_auc = m["train_auc"]
        f1 = m["f1_score"]
        gap = train_auc - roc_auc

        # Solo consideramos corridas con buen desempeño
        if roc_auc >= 0.80 and f1 >= 0.80:      # umbrales algo más bajos
            score = roc_auc - gap
            if score > best_score:
                best_score = score
                best_run = run
                logging.info(f"🏆 Mejor corrida encontrada: {run.info.run_id} con ROC AUC {roc_auc:.4f}, "
                             f"F1 Score {f1:.4f}, Gap {gap:.4f}")

    # 4) Registrar si encontramos uno
    if best_run:
        run_id = best_run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        if not modelo_ya_registrado(MODELO_REGISTRADO, run_id):
            client.set_tag(run_id, "best_model", "true")
            result = mlflow.register_model(model_uri=model_uri, name=MODELO_REGISTRADO)
            logging.info(f"✅ Registrado modelo '{MODELO_REGISTRADO}' versión {result.version}")
        else:
            logging.info("ℹ️ El mejor modelo ya estaba registrado.")
    else:
        logging.error("❌ El modelo no cumple con los umbrales de calidad requeridos.")
