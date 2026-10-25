from sqlalchemy import Column, Integer, Float, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base


class WindForecast(Base):
    __tablename__ = "wind_forecast"

    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time_utc = Column(DateTime(timezone=True), nullable=False)
    publish_time_utc = Column(DateTime(timezone=True), nullable=False)
    generation = Column(Float, nullable=False)
    source_dataset = Column(String(20), nullable=False, default="WINDFOR")
    retrieved_at_utc = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("start_time_utc", "publish_time_utc", name="uq_wind_forecast"),
    )
