# 📉 Churn Prediction System – AI & Big Data Project

Este repositorio contiene el desarrollo completo de un sistema predictivo para anticipar la baja (*churn*) de clientes en una compañía de telecomunicaciones. Es el proyecto final del Curso de Especialización en Inteligencia Artificial y Big Data.

---

## 🚀 Objetivo del Proyecto

Desarrollar una solución integral de IA capaz de predecir clientes en riesgo de abandono, mediante un sistema escalable que funcione en:

- 🧪 Entrenamiento batch  
- 🟢 Inferencia batch (FastAPI + TimescaleDB)  
- ⚡ Inferencia en streaming en tiempo real (Kafka + MongoDB)

---

## 🧠 Tecnologías y Herramientas

- **Python** (Pandas, Scikit-learn, Seaborn, etc.)
- **Modelos:** RandomForest, XGBoost, CatBoost, SVC, LogisticRegression
- **Optuna** para optimización de hiperparámetros
- **MLflow** para seguimiento de experimentos y versionado
- **FastAPI** para servir el modelo en producción
- **Apache Kafka** para procesamiento de datos en streaming
- **Apache Airflow** para orquestación de pipelines
- **Docker + Docker Compose** para contenerización
- **TimescaleDB** para almacenamiento de predicciones batch
- **MongoDB** para almacenamiento de resultados en streaming
- **Jupyter Notebooks** para EDA y prototipado

---

## 🏗️ Arquitectura General

El sistema se divide en tres bloques principales: entrenamiento, inferencia batch e inferencia en tiempo real.

### 🔧 Entrenamiento
- Análisis exploratorio (EDA)
- Preprocesamiento de datos
- Entrenamiento de modelos
- Registro y seguimiento con MLflow

### 🟢 Producción Batch
- FastAPI recibe los datos
- Realiza inferencias
- Guarda las predicciones en TimescaleDB
- Validación externa de calidad

### ⚡ Producción Streaming
- Airflow extrae datos desde un endpoint externo
- Kafka los distribuye
- Un consumidor en Docker los preprocesa
- FastAPI predice en tiempo real
- Kafka reenvía los resultados
- MongoDB almacena las predicciones

---

## 🧪 Resultados

- **Modelo final:** RandomForestClassifier  
- **AUC:** 0.9694  
- **F1-score:** 0.906  
- **Recall:** 0.968  
- Optimizado con **Optuna** y validado con **MLflow**

---

## 📁 Estructura del Repositorio

```
📦 churn-prediction-ia/
├── Code/
│   ├── airflow/dags/           ← DAGs para entrenamiento e inferencia
│   ├── docker/                 ← Configuración de servicios
│   ├── fastapi/                ← API REST para inferencia
│   └── dockerfiles/            ← Consumers y conectores
├── datos/                      ← Datasets y artefactos serializados
├── notebooks/                  ← EDA y análisis exploratorio
├── requirements.txt
└── README.md
```

---

## ▶️ Cómo Ejecutar (Versión Local)

1. Clona el repositorio:

   ```bash
   git clone https://github.com/raulmarquez93/churn-prediction-ia.git
   cd churn-prediction-ia
   ```

2. Levanta los servicios dockerizados:

   ```bash
   docker-compose up --build
   ```

3. Asegúrate de tener **MLflow** instalado y ejecútalo localmente para registrar los experimentos.

---

## 🔒 Aviso

Este es un proyecto académico. Los datos utilizados han sido modificados o generados con fines educativos. No representan información real de clientes.

---

## 📬 Contacto

- 📧 raulmarquez93@gmail.com  
- 🔗 [LinkedIn – Raúl Márquez Roig](https://www.linkedin.com/in/raulmarquez93/)

---

## 🧠 Créditos

Proyecto desarrollado como Trabajo Final del  
**Curso de Especialización en Inteligencia Artificial y Big Data**  
👨‍🏫 Director: **Sergi Pérez Castaños**  
📅 **Junio 2025**

---

