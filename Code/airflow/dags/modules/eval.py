
def evaluar_modelo(**kwargs):
    import pandas as pd
    import pickle
    import base64
    from sklearn.metrics import accuracy_score, classification_report

    ti = kwargs['ti']
    modelo_b64 = ti.xcom_pull(task_ids='entrenar_modelo', key='modelo_entrenado')
    modelo_bytes = base64.b64decode(modelo_b64.encode('utf-8'))
    clf = pickle.loads(modelo_bytes)

    X_test = pd.DataFrame(ti.xcom_pull(task_ids='entrenar_modelo', key='X_test'))
    y_test = pd.Series(ti.xcom_pull(task_ids='entrenar_modelo', key='y_test'))

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print(f" Accuracy: {acc:.4f}")
    print(report)

    ti.xcom_push(key='accuracy', value=acc)