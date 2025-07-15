from typing import List, Optional, Dict, Any
from sqlalchemy import func, extract, text, select, update, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.orm_models import HorasPlanejadas, AlocacaoRecursoProjeto
from app.repositories.base_repository import BaseRepository
from app.schemas.matriz_planejamento_schemas import PlanejamentoHorasCreate

class PlanejamentoHorasRepository(BaseRepository[HorasPlanejadas]):

    def __init__(self, db: AsyncSession):
        super().__init__(db, HorasPlanejadas)

    def _to_dict(self, obj: HorasPlanejadas) -> Dict[str, Any]:
        """Converte um objeto ORM para um dicionário seguro."""
        if not obj:
            return None
        return {
            "id": obj.id,
            "alocacao_id": obj.alocacao_id,
            "ano": obj.ano,
            "mes": obj.mes,
            "horas_planejadas": float(obj.horas_planejadas)
        }

    async def create(self, data: PlanejamentoHorasCreate) -> Dict[str, Any]:
        """Cria um novo registro e retorna um dicionário."""
        db_obj = self.model(**data.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return self._to_dict(db_obj)

    async def update(self, id: int, data: dict) -> Optional[Dict[str, Any]]:
        """Atualiza um registro e retorna um dicionário."""
        if not data:
            obj = await self.get_by_id(id)
            return self._to_dict(obj)

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        obj = result.scalars().first()
        return self._to_dict(obj)

    async def get_by_alocacao_ano_mes(self, alocacao_id: int, ano: int, mes: int) -> Optional[Dict[str, Any]]:
        """Obtém planejamento por alocação, ano e mês, como um dicionário."""
        query = select(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        )
        result = await self.db.execute(query)
        obj = result.scalars().first()
        return self._to_dict(obj)

    async def create_or_update(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
        """Cria ou atualiza um planejamento e retorna um dicionário."""
        existing_dict = await self.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
        
        if existing_dict:
            return await self.update(existing_dict["id"], {"horas_planejadas": horas_planejadas})
        else:
            novo_schema = PlanejamentoHorasCreate(
                alocacao_id=alocacao_id,
                ano=ano,
                mes=mes,
                horas_planejadas=horas_planejadas
            )
            return await self.create(novo_schema)
    
    async def list_by_alocacao(self, alocacao_id: int, ano: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lista todos os planejamentos de uma alocação, retornando uma lista de dicionários."""
        query = select(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id
        )
        if ano is not None:
            query = query.filter(HorasPlanejadas.ano == ano)
        query = query.order_by(HorasPlanejadas.ano, HorasPlanejadas.mes)
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