from requests.auth import HTTPBasicAuth
import requests
import time

clientes_path = "/opt/airflow/dags/data/clientes.csv"
servicios_path = "/opt/airflow/dags/data/servicios.xlsx"
conf = {
        "clientes_path": clientes_path,
        "servicios_path": servicios_path,
}

response = requests.post(
    "http://localhost:8080/api/v1/dags/inferencia/dagRuns",  
    auth=HTTPBasicAuth("admin", "admin"),
    json={"conf": conf}
)

print("Lanzando inferencia con conf:", conf)
print("Código de respuesta:", response.status_code)
print("Respuesta:", response.text)
