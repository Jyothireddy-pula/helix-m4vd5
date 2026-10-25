from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base


class ActualGeneration(Base):
    __tablename__ = "actual_generation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time_utc = Column(DateTime(timezone=True), nullable=False)
    settlement_date = Column(String(10), nullable=False)
    settlement_period = Column(Integer, nullable=False)
    fuel_type = Column(String(20), nullable=False, default="WIND")
    generation = Column(Float, nullable=False)
    source_dataset = Column(String(20), nullable=False, default="FUELHH")
    retrieved_at_utc = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("settlement_date", "settlement_period", "fuel_type", name="uq_actual_gen"),
    )
