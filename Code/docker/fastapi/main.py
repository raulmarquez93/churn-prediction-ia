import mlflow
from mlflow.tracking import MlflowClient
import pandas as pd
from fastapi import FastAPI, HTTPException
from typing import List, Dict
from pydantic import RootModel

# Configurar MLflow
MLFLOW_TRACKING_URI = "http://host.docker.internal:5000"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
REGISTERED_MODEL_NAME = "prediccion_abandono"

# Cliente para interactuar con el registro
client = MlflowClient()

def get_latest_model_version(model_name: str) -> int:
    versions = client.search_model_versions(f"name='{model_name}'")
    active_versions = [v for v in versions if v.current_stage != 'Archived']
    version_numbers = [int(v.version) for v in active_versions]
    if not version_numbers:
        raise ValueError(f"No se encontraron versiones activas para el modelo '{model_name}'")
    return max(version_numbers)

# Obtener dinámicamente la última versión y cargar el modelo
latest_version = get_latest_model_version(REGISTERED_MODEL_NAME)
model_uri = f"models:/{REGISTERED_MODEL_NAME}/{latest_version}"
model = mlflow.pyfunc.load_model(model_uri=model_uri)

# Configuración de FastAPI
app = FastAPI()
predictions_history = []

class Item(RootModel[List[Dict]]):
    """Modelo raíz que envuelve una lista de diccionarios de entrada"""
    pass

@app.get("/")
def root():
    return {"message": f"Model '{REGISTERED_MODEL_NAME}' version {latest_version} loaded successfully!"}

@app.post("/predict")
def predict(data: Item):
    try:
        df = pd.DataFrame(data.root)
        preds = model.predict(df)
        pred_list = preds.tolist()

        for inp, p in zip(data.root, pred_list):
            predictions_history.append({"input": inp, "prediction": p})

        return {"predictions": pred_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/results")
def get_predictions():
    return {"history": predictions_history}
