from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orm_models import HorasPlanejadas, AlocacaoRecursoProjeto
from app.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class PlanejamentoHorasRepository(BaseRepository):
    def __init__(self, db: AsyncSession):
        super().__init__(db, HorasPlanejadas)

    async def get_by_alocacao_ano_mes(self, alocacao_id: int, ano: int, mes: int) -> Optional[HorasPlanejadas]:
        query = select(HorasPlanejadas).where(
            HorasPlanejadas.alocacao_id == alocacao_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_or_update(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
        logger.debug(f"Iniciando create_or_update para alocacao_id={alocacao_id}, ano={ano}, mes={mes}")
        existing = await self.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
        
        try:
            if existing:
                logger.info(f"Atualizando planejamento existente ID={existing.id} com {horas_planejadas} horas.")
                stmt = (
                    update(HorasPlanejadas)
                    .where(HorasPlanejadas.id == existing.id)
                    .values(horas_planejadas=horas_planejadas)
                    .returning(HorasPlanejadas)
                )
                result = await self.db.execute(stmt)
                await self.db.commit()
                updated_obj = result.scalar_one()
                logger.info(f"Planejamento ID={updated_obj.id} atualizado com sucesso.")
                return updated_obj.to_dict()
            else:
                logger.info(f"Criando novo planejamento para alocacao_id={alocacao_id}, ano={ano}, mes={mes}.")
                new_obj = HorasPlanejadas(
                    alocacao_id=alocacao_id,
                    ano=ano,
                    mes=mes,
                    horas_planejadas=horas_planejadas
                )
                self.db.add(new_obj)
                await self.db.flush()
                await self.db.commit()
                await self.db.refresh(new_obj)
                logger.info(f"Novo planejamento ID={new_obj.id} criado com sucesso.")
                return new_obj.to_dict()
        except Exception as e:
            logger.error(f"Erro em create_or_update para alocacao_id={alocacao_id}: {e}", exc_info=True)
            await self.db.rollback()
            raise

    async def list_by_alocacao(self, alocacao_id: int, ano: Optional[int] = None) -> List[HorasPlanejadas]:
        query = select(HorasPlanejadas).where(HorasPlanejadas.alocacao_id == alocacao_id)
        if ano:
            query = query.where(HorasPlanejadas.ano == ano)
        result = await self.db.execute(query)
        orm_objects = result.scalars().all()
        return [self._to_dict(obj) for obj in orm_objects]
    
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

    async def get_matriz_data_by_recurso(self, recurso_id: int) -> List[Dict[str, Any]]:
        """
        Busca os dados brutos para a montagem da matriz de planejamento de um recurso.
        Retorna uma lista de dicionários, cada um representando uma linha de dados
        combinando alocação e planejamento mensal (se houver).
        """
        query = text("""
            SELECT
                p.id as projeto_id,
                a.id as alocacao_id,
                a.status_alocacao_id,
                a.observacao,
                a.esforco_estimado,
                hp.ano,
                hp.mes,
                hp.horas_planejadas
            FROM
                projeto p
            INNER JOIN LATERAL (
                SELECT *
                FROM alocacao_recurso_projeto a2
                WHERE a2.projeto_id = p.id AND a2.recurso_id = :recurso_id
                ORDER BY a2.data_inicio_alocacao DESC
                LIMIT 1
            ) a ON TRUE
            LEFT JOIN horas_planejadas_alocacao hp ON a.id = hp.alocacao_id
            ORDER BY p.id, hp.ano, hp.mes
        """)
        
        result = await self.db.execute(query, {"recurso_id": recurso_id})
        return [dict(row._mapping) for row in result.all()]