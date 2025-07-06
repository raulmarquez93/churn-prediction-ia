def entrenar_modelo(**kwargs):
    import optuna
    import pickle, base64, pandas as pd, os
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
    from sklearn.metrics import (
        roc_auc_score, accuracy_score, precision_score,
        recall_score, f1_score, confusion_matrix
    )
    from xgboost import XGBClassifier
    from catboost import CatBoostClassifier

    ti = kwargs['ti']
    conf = kwargs.get("dag_run").conf or {}
    use_cv = conf.get("validacion_cruzada", False)
    modelo_fijo = conf["modelo_fijo"]  # obligatorio ahora

    df = pd.DataFrame(ti.xcom_pull(task_ids='transformacion_final', key='datos_finales'))
    X = df.drop(columns=['abandono'])
    y = df['abandono']

    def objective(trial):
        modelo = modelo_fijo

        if modelo == "RandomForest":
            clf = RandomForestClassifier(
                n_estimators=trial.suggest_int("n_estimators", 50, 150),
                max_depth=trial.suggest_int("max_depth", 3, 15),
                random_state=42
            )
        elif modelo == "LogisticRegression":
            clf = LogisticRegression(
                C=trial.suggest_float("C", 0.01, 10.0),
                max_iter=1000,
                solver="lbfgs"
            )
        elif modelo == "SVC":
            clf = SVC(
                C=trial.suggest_float("C", 0.01, 10.0),
                kernel=trial.suggest_categorical("kernel", ["linear", "rbf"]),
                probability=True
            )
        elif modelo == "XGBoost":
            clf = XGBClassifier(
                n_estimators=trial.suggest_int("n_estimators", 50, 150),
                max_depth=trial.suggest_int("max_depth", 3, 10),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3),
                use_label_encoder=False,
                eval_metric="logloss"
            )

        else:  # CatBoost
            clf = CatBoostClassifier(
                iterations=trial.suggest_int("iterations", 50, 150),
                depth=trial.suggest_int("depth", 3, 10),
                learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3),
                verbose=0
            )

        if use_cv:
            print("Usando validación cruzada")
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_validate(
                clf, X, y, cv=cv,
                scoring="roc_auc",
                return_train_score=True
            )
            trial.set_user_attr("train_auc", scores["train_score"].mean())
            trial.set_user_attr("val_auc", scores["test_score"].mean())
            return scores["test_score"].mean()
        else:
            print("Usando división simple de entrenamiento y prueba")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            clf.fit(X_train, y_train)
            y_prob = clf.predict_proba(X_test)[:, 1]
            return roc_auc_score(y_test, y_prob)

    study = optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner(n_startup_trials=10))
    study.optimize(objective, n_trials=50)

    train_auc = study.best_trial.user_attrs.get("train_auc")
    val_auc = study.best_trial.user_attrs.get("val_auc")
    diferencia_auc = val_auc - train_auc

    ti.xcom_push(key='optuna_train_auc', value=train_auc)
    ti.xcom_push(key='optuna_auc_diff', value=diferencia_auc)

    best_params = study.best_params
    best_score = study.best_value

    if modelo_fijo == "RandomForest":
        model = RandomForestClassifier(**best_params, random_state=42)
    elif modelo_fijo == "LogisticRegression":
        model = LogisticRegression(**best_params, max_iter=1000, solver="lbfgs")
    elif modelo_fijo == "SVC":
        model = SVC(**best_params, probability=True)
    elif modelo_fijo == "XGBoost":
        model = XGBClassifier(**best_params, use_label_encoder=False, eval_metric="logloss")

    else:
        model = CatBoostClassifier(**best_params, verbose=0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc_test = roc_auc_score(y_test, y_prob)
    acc = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    ti.xcom_push(key='auc_test', value=auc_test)
    ti.xcom_push(key='accuracy', value=acc)
    ti.xcom_push(key='precision', value=precision)
    ti.xcom_push(key='recall', value=recall)
    ti.xcom_push(key='f1_score', value=f1)

    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Matriz de Confusión")
    confusion_path = "/opt/airflow/dags/data/matriz_confusion.png"
    plt.savefig(confusion_path)
    plt.close()

    ti.xcom_push(key='confusion_matrix_path', value=confusion_path)

    modelo_b64 = base64.b64encode(pickle.dumps(model)).decode('utf-8')
    ti.xcom_push(key='modelo_entrenado', value=modelo_b64)
    ti.xcom_push(key='X_test', value=X_test.to_dict(orient='records'))
    ti.xcom_push(key='y_test', value=y_test.tolist())
    ti.xcom_push(key='optuna_best_params', value=best_params)
    ti.xcom_push(key='optuna_auc', value=best_score)

    study_path = "/opt/airflow/dags/data/optuna_study.pkl"
    with open(study_path, "wb") as f:
        pickle.dump(study, f)
    ti.xcom_push(key='optuna_study_path', value=study_path)

    import optuna.visualization.matplotlib as vis
    fig1 = vis.plot_optimization_history(study)
    fig1_path = "/opt/airflow/dags/data/optuna_history.png"
    fig1.figure.savefig(fig1_path)

    fig2 = vis.plot_param_importances(study)
    fig2_path = "/opt/airflow/dags/data/optuna_importances.png"
    fig2.figure.savefig(fig2_path)

    ti.xcom_push(key='optuna_plot_history', value=fig1_path)
    ti.xcom_push(key='optuna_plot_importances', value=fig2_path)

    print(f" Modelo {modelo_fijo} entrenado con Optuna. Mejor AUC: {best_score:.4f}")