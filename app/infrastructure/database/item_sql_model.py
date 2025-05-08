from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.database_config import Base

class ItemSQL(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    description = Column(String, index=True)
    # Add created_at and updated_at for good practice, though not in original simple model
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

