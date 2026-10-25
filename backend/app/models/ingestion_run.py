from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_run"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running, success, failed
    records_fetched = Column(Integer, default=0)
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    error_summary = Column(Text, nullable=True)
