import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_tracking_uri("http://host.docker.internal:5000")
client = MlflowClient()

MODEL_NAME = "modelo_produccion_optimo"
VERSION = 2  # Asegúrate de que esta sea la versión correcta

# Promover a Production
client.transition_model_version_stage(
    name=MODEL_NAME,
    version=str(VERSION),
    stage="Production",
    archive_existing_versions=True  # Opcional: archiva versiones anteriores en Production
)

print(f"✅ Modelo '{MODEL_NAME}' versión {VERSION} promovido a 'Production'.")
