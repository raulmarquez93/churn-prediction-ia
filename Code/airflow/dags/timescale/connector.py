from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

Base = declarative_base()

class Model(Base):
    __tablename__ = "models"
    model_id       = Column(Integer, primary_key=True)
    model_name     = Column(String(255), nullable=False)
    model_version  = Column(Integer, nullable=False)
    mlflow_run_id  = Column(String(255))
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    parameters     = Column(JSONB)
    metrics        = Column(JSONB)

    predictions    = relationship("Prediction", back_populates="model")

    __table_args__ = (
        Index('idx_model_name_version', 'model_name', 'model_version', unique=True),
    )

class Prediction(Base):
    __tablename__ = "predictions"
    prediction_id    = Column(Integer, primary_key=True)
    model_id         = Column(Integer, ForeignKey("models.model_id"), nullable=False)
    prediction_time  = Column(DateTime(timezone=True), server_default=func.now())
    input_data       = Column(JSONB)
    prediction_value = Column(Float, nullable=False)

    model            = relationship("Model", back_populates="predictions")

    __table_args__ = (
        Index('idx_predictions_model_id', 'model_id'),
    )
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TimescaleDBConnector:
    def __init__(self,
                 host: str = "timescaledb",
                 port: int = 5432,
                 user: str = "postgres",
                 password: str = "postgres",
                 database: str = "timescale"):
        uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(uri, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)

    def init_db(self):
        # Solo la primera vez, para crear las tablas ORM (no la hypertable)
        Base.metadata.create_all(self.engine)
