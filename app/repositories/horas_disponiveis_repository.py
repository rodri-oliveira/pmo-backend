from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.orm_models import HorasDisponiveisRH
from app.repositories.base_repository import BaseRepository

class HorasDisponiveisRepository(BaseRepository[HorasDisponiveisRH, int]):
    """Repositório para operações com a entidade HorasDisponiveisRH."""
    
    def __init__(self, db: Session):
        super().__init__(db, HorasDisponiveisRH)
    
    def get_by_recurso_ano_mes(self, recurso_id: int, ano: int, mes: int) -> Optional[HorasDisponiveisRH]:
        """Obtém registro de horas disponíveis por recurso, ano e mês."""
        return self.db.query(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.recurso_id == recurso_id,
            HorasDisponiveisRH.ano == ano,
            HorasDisponiveisRH.mes == mes
        ).first()
    
    def create_or_update(self, recurso_id: int, ano: int, mes: int, horas_disponiveis: float) -> HorasDisponiveisRH:
        """Cria ou atualiza um registro de horas disponíveis."""
        existing = self.get_by_recurso_ano_mes(recurso_id, ano, mes)
        
        if existing:
            # Atualizar existente
            existing.horas_disponiveis_mes = horas_disponiveis
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Criar novo
            return self.create({
                "recurso_id": recurso_id,
                "ano": ano,
                "mes": mes,
                "horas_disponiveis_mes": horas_disponiveis
            })
    
    def list_by_recurso(self, recurso_id: int) -> List[HorasDisponiveisRH]:
        """Lista todos os registros de horas disponíveis para um recurso."""
        return self.db.query(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.recurso_id == recurso_id
        ).order_by(HorasDisponiveisRH.ano, HorasDisponiveisRH.mes).all()
    
    def list_by_ano_mes(self, ano: int, mes: int) -> List[HorasDisponiveisRH]:
        """Lista todos os registros de horas disponíveis para um mês/ano específico."""
        return self.db.query(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.ano == ano,
            HorasDisponiveisRH.mes == mes
        ).all() 