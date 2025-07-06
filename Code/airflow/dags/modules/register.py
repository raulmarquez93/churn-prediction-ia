def registrar_modelo_en_mlflow(**kwargs):
    import mlflow, base64, pickle, os, pandas as pd

    ti = kwargs['ti']
    conf = kwargs['dag_run'].conf

    # 🔁 Pulls de entrenamiento y transformación
    modelo_b64 = ti.xcom_pull(task_ids='entrenar_modelo', key='modelo_entrenado')
    auc = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_auc')
    accuracy = ti.xcom_pull(task_ids='entrenar_modelo', key='accuracy')
    precision = ti.xcom_pull(task_ids='entrenar_modelo', key='precision')
    recall = ti.xcom_pull(task_ids='entrenar_modelo', key='recall')
    f1_score = ti.xcom_pull(task_ids='entrenar_modelo', key='f1_score')
    auc_test = ti.xcom_pull(task_ids='entrenar_modelo', key='auc_test')
    train_auc = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_train_auc')
    diferencia_auc = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_auc_diff')
    optuna_best_params = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_best_params')
    df_final = ti.xcom_pull(task_ids='transformacion_final', key='datos_finales')

    # 🔐 Modelo entrenado
    modelo_bytes = base64.b64decode(modelo_b64.encode('utf-8'))
    clf = pickle.loads(modelo_bytes)

    # 🎯 Configurar MLflow
    mlflow.set_tracking_uri("http://host.docker.internal:5000")
    mlflow.set_experiment("prediccion_abandono")

    with mlflow.start_run(run_name=f"{clf.__class__.__name__}_AUC_{auc:.4f}"):
        # 🧾 Parámetros
        mlflow.log_param("modelo", clf.__class__.__name__)
        for key, val in conf.items():
            mlflow.log_param(f"conf_{key}", val)
        for key, val in optuna_best_params.items():
            mlflow.log_param(f"optuna_{key}", val)

        # 📊 Métricas
        mlflow.log_metric("roc_auc", auc)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1_score)
        mlflow.log_metric("auc_test", auc_test)
        mlflow.log_metric("train_auc", train_auc)
        mlflow.log_metric("diferencia_auc", diferencia_auc)

        # 💾 Modelo manual serializado
        model_path = "artifacts/modelo_entrenado.pkl"
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(clf, f)
        mlflow.log_artifact(model_path, artifact_path="modelo_manual")

        # 📄 Dataset final
        dataset_path = "artifacts/dataset_final.csv"
        df_final.to_csv(dataset_path, index=False)
        mlflow.log_artifact(dataset_path, artifact_path="dataset_final")

        # 🧰 Artefactos de transformación
        scaler_path = ti.xcom_pull(task_ids='transformacion_final', key='scaler_path')
        columnas_path = ti.xcom_pull(task_ids='transformacion_final', key='columnas_path')
        kbest_path = ti.xcom_pull(task_ids='transformacion_final', key='kbest_path')
        label_encoders_path = ti.xcom_pull(task_ids='transformacion_final', key='label_encoders_path')

        if scaler_path and os.path.exists(scaler_path):
            mlflow.log_artifact(scaler_path, artifact_path="scaler")
        if columnas_path and os.path.exists(columnas_path):
            mlflow.log_artifact(columnas_path, artifact_path="columnas")
        if kbest_path and os.path.exists(kbest_path):
            mlflow.log_artifact(kbest_path, artifact_path="kbest")
        if label_encoders_path and os.path.exists(label_encoders_path):
            mlflow.log_artifact(label_encoders_path, artifact_path="label_encoders")

        # 📈 Visualizaciones de Optuna
        optuna_study_path = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_study_path')
        optuna_plot_history = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_plot_history')
        optuna_plot_importances = ti.xcom_pull(task_ids='entrenar_modelo', key='optuna_plot_importances')

        for optuna_art in [optuna_study_path, optuna_plot_history, optuna_plot_importances]:
            if optuna_art and os.path.exists(optuna_art):
                mlflow.log_artifact(optuna_art, artifact_path="optuna")

        # 🔍 Matriz de confusión
        confusion_matrix_path = ti.xcom_pull(task_ids='entrenar_modelo', key='confusion_matrix_path')
        if confusion_matrix_path and os.path.exists(confusion_matrix_path):
            mlflow.log_artifact(confusion_matrix_path, artifact_path="evaluacion")

        # 🚀 Registro modelo MLflow compatible
        mlflow.sklearn.log_model(clf, artifact_path="model")

    
