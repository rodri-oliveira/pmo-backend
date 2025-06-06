from sqlalchemy import Column, Integer, SmallInteger, Date, Boolean, String
from app.infrastructure.database.database_config import Base

class DimTempoSQL(Base):
    __tablename__ = "dim_tempo"

    data_id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, unique=True, nullable=False, index=True)
    ano = Column(SmallInteger, nullable=False)
    mes = Column(Integer, nullable=False)
    dia = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)
    nome_dia_semana = Column(String(20), nullable=False)
    nome_mes = Column(String(20), nullable=False)
    semana_ano = Column(Integer, nullable=False)
    is_dia_util = Column(Boolean, nullable=False)
    is_feriado = Column(Boolean, nullable=False)
    nome_feriado = Column(String(100), nullable=True)
