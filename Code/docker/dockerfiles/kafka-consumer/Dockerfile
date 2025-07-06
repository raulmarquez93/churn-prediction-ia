FROM python:3.9-slim

WORKDIR /app
COPY artifacts ./artifacts/
COPY consumer.py .

RUN pip install kafka-python  pandas  requests scikit-learn numpy  joblib

CMD ["python", "consumer.py"]
