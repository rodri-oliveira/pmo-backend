from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orm_models import Apontamento, Recurso, Equipe, Secao, Projeto, HorasDisponiveisRH, equipe_projeto_association
from app.repositories.apontamento_repository import ApontamentoRepository

def get_groupby_columns(agrupar_por):
    columns = []
    if not agrupar_por:
        return columns
    if "recurso" in agrupar_por:
        columns.append(Recurso.id.label("recurso_id"))
        columns.append(Recurso.nome.label("recurso_nome"))
    if "equipe" in agrupar_por:
        columns.append(Equipe.id.label("equipe_id"))
        columns.append(Equipe.nome.label("equipe_nome"))
    if "secao" in agrupar_por:
        columns.append(Secao.id.label("secao_id"))
        columns.append(Secao.nome.label("secao_nome"))
    if "projeto" in agrupar_por:
        columns.append(Projeto.id.label("projeto_id"))
        columns.append(Projeto.nome.label("projeto_nome"))
    if "mes" in agrupar_por:
        columns.append(extract('month', Apontamento.data_apontamento).label("mes"))
    if "ano" in agrupar_por:
        columns.append(extract('year', Apontamento.data_apontamento).label("ano"))
    return columns

class RelatorioDinamicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_relatorio(
        self,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        projeto_id: Optional[int] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        agrupar_por: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        repo = ApontamentoRepository(self.db)
        return await repo.find_with_filters_and_aggregate(
            recurso_id=recurso_id,
            projeto_id=projeto_id,
            equipe_id=equipe_id,
            secao_id=secao_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            agrupar_por_recurso="recurso" in agrupar_por,
            agrupar_por_projeto="projeto" in agrupar_por,
            agrupar_por_data="data" in agrupar_por,
            agrupar_por_mes="mes" in agrupar_por,
            aggregate=True
        )

    async def get_horas_disponiveis(self, recurso_id: Optional[int] = None, ano: Optional[int] = None, mes: Optional[int] = None) -> List[Dict[str, Any]]:
        query = select(HorasDisponiveisRH.recurso_id, HorasDisponiveisRH.ano, HorasDisponiveisRH.mes, HorasDisponiveisRH.horas_disponiveis_mes)
        if recurso_id:
            query = query.where(HorasDisponiveisRH.recurso_id == recurso_id)
        if ano:
            query = query.where(HorasDisponiveisRH.ano == ano)
        if mes:
            query = query.where(HorasDisponiveisRH.mes == mes)
        result = await self.db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
