from typing import List, Optional, Dict, Any
from sqlalchemy import func, extract, text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.orm_models import HorasPlanejadas, AlocacaoRecursoProjeto
from app.repositories.base_repository import BaseRepository

class PlanejamentoHorasRepository(BaseRepository[HorasPlanejadas]):
    """Repositório para planejamento de horas."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, HorasPlanejadas)
    
    async def get_by_alocacao_ano_mes(self, alocacao_id: int, ano: int, mes: int) -> Optional[HorasPlanejadas]:
        """Obtém planejamento por alocação, ano e mês."""
        query = select(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def create_or_update(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> HorasPlanejadas:
        """Cria ou atualiza um planejamento de horas."""
        existing = await self.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
        
        if existing:
            # Atualizar existente
            existing.horas_planejadas = horas_planejadas
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Criar novo
            return await self.create({
                "alocacao_id": alocacao_id,
                "ano": ano,
                "mes": mes,
                "horas_planejadas": horas_planejadas
            })
    
    async def list_by_alocacao(self, alocacao_id: int) -> List[HorasPlanejadas]:
        """Lista todos os planejamentos de uma alocação."""
        query = select(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id
        ).order_by(HorasPlanejadas.ano, HorasPlanejadas.mes)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_by_recurso_periodo(self, recurso_id: int, ano: int, mes_inicio: int = 1, mes_fim: int = 12) -> List[Dict[str, Any]]:
        """Lista planejamentos de um recurso em um período."""
        # Usar SQL nativo para obter os dados mais facilmente
        sql = text("""
            SELECT 
                hp.id, 
                hp.alocacao_id, 
                arp.projeto_id, 
                arp.recurso_id, 
                hp.ano, 
                hp.mes, 
                hp.horas_planejadas
            FROM 
                horas_planejadas_alocacao hp
            JOIN 
                alocacao_recurso_projeto arp ON hp.alocacao_id = arp.id
            WHERE 
                arp.recurso_id = :recurso_id
                AND hp.ano = :ano
                AND hp.mes >= :mes_inicio
                AND hp.mes <= :mes_fim
            ORDER BY 
                hp.mes
        """)
        
        result = await self.db.execute(
            sql, 
            {"recurso_id": recurso_id, "ano": ano, "mes_inicio": mes_inicio, "mes_fim": mes_fim}
        )
        
        # Converter para uma lista de dicionários
        return [dict(row._mapping) for row in result.all()]
    
    async def get_total_horas_planejadas_por_recurso_mes(self, recurso_id: int, ano: int, mes: int) -> Optional[float]:
        """Obtém o total de horas planejadas para um recurso em um mês específico."""
        query = select(func.sum(HorasPlanejadas.horas_planejadas).label("total_horas")).join(
            AlocacaoRecursoProjeto,
            HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        )
        result = await self.db.execute(query)
        total_horas = result.scalars().first()
        
        return float(total_horas) if total_horas is not None else None