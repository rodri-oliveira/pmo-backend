from typing import List, Optional, Dict, Any, Tuple
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

    async def list_with_filters_and_pagination(
        self,
        skip: int,
        limit: int,
        filters: Dict[str, Any]
    ) -> Tuple[List[HorasPlanejadas], int]:
        """
        Lista planejamentos com filtros e paginação.

        Args:
            skip: Número de registros a pular.
            limit: Número máximo de registros a retornar.
            filters: Dicionário de filtros (ano, mes, recurso_id, projeto_id).

        Returns:
            Tuple[List[HorasPlanejadas], int]: Lista de planejamentos e contagem total.
        """
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        needs_join = False
        if filters.get("recurso_id") or filters.get("projeto_id"):
            needs_join = True
        
        if needs_join:
            stmt = stmt.join(AlocacaoRecursoProjeto, self.model.alocacao_id == AlocacaoRecursoProjeto.id)
            count_stmt = count_stmt.join(AlocacaoRecursoProjeto, self.model.alocacao_id == AlocacaoRecursoProjeto.id)

        if "ano" in filters:
            stmt = stmt.filter(self.model.ano == filters["ano"])
            count_stmt = count_stmt.filter(self.model.ano == filters["ano"])
        if "mes" in filters:
            stmt = stmt.filter(self.model.mes == filters["mes"])
            count_stmt = count_stmt.filter(self.model.mes == filters["mes"])
        if "recurso_id" in filters:
            stmt = stmt.filter(AlocacaoRecursoProjeto.recurso_id == filters["recurso_id"])
            count_stmt = count_stmt.filter(AlocacaoRecursoProjeto.recurso_id == filters["recurso_id"])
        if "projeto_id" in filters:
            stmt = stmt.filter(AlocacaoRecursoProjeto.projeto_id == filters["projeto_id"])
            count_stmt = count_stmt.filter(AlocacaoRecursoProjeto.projeto_id == filters["projeto_id"])

        # Contagem total
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar_one_or_none() or 0

        # Busca paginada
        stmt = stmt.order_by(self.model.ano, self.model.mes, self.model.id).offset(skip).limit(limit)
        if needs_join: # Garante que os campos da tabela AlocacaoRecursoProjeto não sejam carregados automaticamente como atributos diretos de HorasPlanejadas
            stmt = stmt.options(joinedload(HorasPlanejadas.alocacao))
            
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return items, total_count