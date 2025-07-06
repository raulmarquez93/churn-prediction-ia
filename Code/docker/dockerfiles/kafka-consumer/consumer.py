import os
import json
import pickle
import uuid
import pandas as pd
from kafka import KafkaConsumer, KafkaProducer
import requests

BASE_DIR = os.path.dirname(__file__)
ARTIFACT_DIR = os.path.join(BASE_DIR, "artifacts")

CONF = {
    "metodo_escalado": "standard",
    "usar_kbest": False,
    "metodo_limpieza": "simple",
    "validacion_cruzada": True
}

topic_entrada = 'clientes-dato'
topic_salida = 'predicciones-modelo'
kafka_servers = ['broker:29092']

def cargar_artefactos_local():
    with open(os.path.join(ARTIFACT_DIR, "columnas_entrenamiento.txt"), 'r') as f:
        columnas = f.read().splitlines()

    with open(os.path.join(ARTIFACT_DIR, "scaler.pkl"), 'rb') as f:
        scaler = pickle.load(f)

    with open(os.path.join(ARTIFACT_DIR, "label_encoders.pkl"), 'rb') as f:
        encoders = pickle.load(f)

    kbest_path = os.path.join(ARTIFACT_DIR, "kbest_columnas.txt")
    columnas_kbest = []
    if os.path.exists(kbest_path):
        with open(kbest_path, 'r') as f:
            columnas_kbest = f.read().splitlines()

    print(f"✅ Artefactos cargados desde {ARTIFACT_DIR}")
    return columnas, scaler, encoders, columnas_kbest

def procesar_mensaje(data, artefactos):
    columnas, scaler, encoders, columnas_kbest = artefactos

    # 1) Normalizar todas las claves de 'data' a minúsculas
    data = {k.strip().lower(): v for k, v in data.items()}

    # 2) Extraer 'abandono' usando la clave ya en minúsculas
    abandono = data.pop("abandono", None)

    # 3) Crear DataFrame
    df = pd.DataFrame([data])

    # 4) (Opcional) Limpieza
    if CONF['metodo_limpieza'] == 'simple':
        df = df.dropna()
    elif CONF['metodo_limpieza'] == 'advanced':
        df = df.fillna(df.median(numeric_only=True))
    else:
        raise ValueError(f"Método limpieza desconocido: {CONF['metodo_limpieza']}")

    # 5) Codificar variables categóricas
    for col, encoder in encoders.items():
        if col in df.columns:
            df[col] = encoder.transform(df[col].astype(str))

    # 6) Seleccionar las columnas en minúsculas que cargaste
    df = df[columnas]

    # 7) Escalar
    df_scaled = pd.DataFrame(scaler.transform(df), columns=columnas)

    # 8) (Si usas kbest) Filtrar
    if CONF['usar_kbest'] and columnas_kbest:
        df_scaled = df_scaled[columnas_kbest]

    print("✅ Datos procesados correctamente.")
    return df_scaled, abandono, data

def predecir_y_enviar(df, abandono, original, producer):
    registros = df.to_dict(orient='records')
    url = "http://host.docker.internal:8000/predict"
    print(f"🚀 Enviando datos a FastAPI: {url}")
    res = requests.post(url, json=registros)
    res.raise_for_status()

    predicciones = res.json().get('predictions', [])
    for entrada, pred in zip([original], predicciones):
        mensaje = {
            **entrada,
            "Abandono": abandono,
            "prediccion": pred
        }
        producer.send(topic_salida, value=mensaje)
        print(f"✅ Predicción enviada: {mensaje}")

def main():
    print("🚀 Iniciando consumidor Kafka...")
    artefactos = cargar_artefactos_local()

    consumer = KafkaConsumer(
        topic_entrada,
        bootstrap_servers=kafka_servers,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id=f"inference-abandono-{uuid.uuid4().hex[:6]}"
    )

    producer = KafkaProducer(
        bootstrap_servers=kafka_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    print(f"🟢 Esperando mensajes en '{topic_entrada}'...")
    for message in consumer:
        try:
            data = message.value
            print(f"📩 Mensaje recibido: {data}")
            df_proc, abandono, datos_originales = procesar_mensaje(data, artefactos)
            predecir_y_enviar(df_proc, abandono, datos_originales, producer)
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")

if __name__ == '__main__':
    main()
