from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orm_models import HorasDisponiveisRH
from app.repositories.base_repository import BaseRepository

class HorasDisponiveisRepository(BaseRepository[HorasDisponiveisRH]):
    """Repositório para operações com a entidade HorasDisponiveisRH."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, HorasDisponiveisRH)
    
    async def get_by_recurso_ano_mes(self, recurso_id: int, ano: int, mes: int) -> Optional[HorasDisponiveisRH]:
        """Obtém registro de horas disponíveis por recurso, ano e mês."""
        query = select(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.recurso_id == recurso_id,
            HorasDisponiveisRH.ano == ano,
            HorasDisponiveisRH.mes == mes
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def create_or_update(self, recurso_id: int, ano: int, mes: int, horas_disponiveis: float) -> HorasDisponiveisRH:
        """Cria ou atualiza um registro de horas disponíveis."""
        existing = await self.get_by_recurso_ano_mes(recurso_id, ano, mes)
        
        if existing:
            # Atualizar existente
            existing.horas_disponiveis_mes = horas_disponiveis
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Criar novo
            return await self.create({
                "recurso_id": recurso_id,
                "ano": ano,
                "mes": mes,
                "horas_disponiveis_mes": horas_disponiveis
            })
    
    async def list_by_recurso(self, recurso_id: int) -> List[HorasDisponiveisRH]:
        """Lista todos os registros de horas disponíveis para um recurso."""
        query = select(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.recurso_id == recurso_id
        ).order_by(HorasDisponiveisRH.ano, HorasDisponiveisRH.mes)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_by_ano_mes(self, ano: int, mes: int) -> List[HorasDisponiveisRH]:
        """Lista todos os registros de horas disponíveis para um mês/ano específico."""
        query = select(HorasDisponiveisRH).filter(
            HorasDisponiveisRH.ano == ano,
            HorasDisponiveisRH.mes == mes
        )
        result = await self.db.execute(query)
        return result.scalars().all()