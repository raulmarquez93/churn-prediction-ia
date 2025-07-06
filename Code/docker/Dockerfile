FROM apache/airflow:2.10.4-python3.9

USER root

 
# Instalar MLflow y otras dependencias
COPY requirements.txt ./requirements.txt

USER airflow
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r ./requirements.txt

