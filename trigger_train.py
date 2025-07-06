from requests.auth import HTTPBasicAuth
import requests
import time

clientes_path = "/opt/airflow/dags/data/clientes.csv"
servicios_path = "/opt/airflow/dags/data/servicios.xlsx"

usar_kbest = [True, False]
ks = [5, 10, 15]
escaladores = ["standard", "minmax", "robust"]

# ✅ Lista de modelos a probar
modelos = ["RandomForest", "LogisticRegression", "SVC", "XGBoost", "CatBoost"]

# ✅ Generar solo combinaciones válidas
combinaciones = []

for kbest_flag in usar_kbest:
    if kbest_flag:
        for k in ks:
            for escalador in escaladores:
                combinaciones.append(( kbest_flag, k, escalador))
    else:
        for escalador in escaladores:
            combinaciones.append(( kbest_flag, 0, escalador))  # k=0 si no se usa

# ▶️ Lanzar ejecuciones a Airflow por cada modelo y combinación
total_runs = len(modelos) * len(combinaciones)
run_idx = 1

for modelo in modelos:
    for  kbest_flag, k, escalador in combinaciones:
        conf = {
            "clientes_path": clientes_path,
            "servicios_path": servicios_path,
            "usar_kbest": kbest_flag,
            "k": k,
            "metodo_escalado": escalador,
            "validacion_cruzada": True,
            "modelo_fijo": modelo  
        }

        response = requests.post(
            "http://localhost:8080/api/v1/dags/entrenamiento/dagRuns",
            auth=HTTPBasicAuth("admin", "admin"),
            json={"conf": conf}
        )

        print(f"▶️ Lanzando ejecución {run_idx}/{total_runs} con modelo {modelo} y conf: {conf}")
        print("Código de respuesta:", response.status_code)
        print("Respuesta:", response.text)

        run_idx += 1
        if run_idx <= total_runs:
            print("⏳ Esperando 1 segundos antes de la siguiente ejecución...")
            time.sleep(1)
