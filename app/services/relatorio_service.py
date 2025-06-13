from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import func, and_, or_, text, extract, select, join

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import (
    Apontamento, 
    Recurso, 
    Projeto, 
    Equipe, 
    Secao, 
    AlocacaoRecursoProjeto, 
    HorasPlanejadas,
    HorasDisponiveisRH
)

class RelatorioService:
    """
    Serviço para geração de relatórios e análises do sistema.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa o serviço com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados assíncrona
        """
        self.db = db
    
    async def get_horas_por_projeto(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None,
        secao_id: Optional[int] = None,
        equipe_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém o total de horas apontadas por projeto.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            secao_id: Filtrar por seção
            equipe_id: Filtrar por equipe
            
        Returns:
            Lista de dicionários com informações de horas por projeto
        """
        query = select(
            Projeto.id.label("projeto_id"),
            Projeto.nome.label("projeto_nome"),
            Projeto.codigo_empresa.label("projeto_codigo"),
            func.sum(Apontamento.horas_apontadas).label("total_horas")
        ).join(
            Apontamento, Apontamento.projeto_id == Projeto.id
        ).group_by(
            Projeto.id, Projeto.nome, Projeto.codigo_empresa
        )
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
            
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
            
        if secao_id or equipe_id:
            query = query.join(
                Recurso, Apontamento.recurso_id == Recurso.id
            )
            
            if secao_id:
                query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                query = query.filter(Equipe.secao_id == secao_id)
                
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "projeto_id": row.projeto_id,
                "projeto_nome": row.projeto_nome,
                "projeto_codigo": row.projeto_codigo,
                "total_horas": float(row.total_horas) if row.total_horas else 0
            }
            for row in rows
        ]
    
    async def get_horas_por_recurso(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None,
        projeto_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém o total de horas apontadas por recurso.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            projeto_id: Filtrar por projeto
            equipe_id: Filtrar por equipe
            secao_id: Filtrar por seção
            
        Returns:
            Lista de dicionários com informações de horas por recurso
        """
        query = select(
            Recurso.id.label("recurso_id"),
            Recurso.nome.label("recurso_nome"),
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome"),
            func.sum(Apontamento.horas_apontadas).label("total_horas")
        ).join(
            Apontamento, Apontamento.recurso_id == Recurso.id
        ).join(
            Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True
        ).join(
            Secao, Equipe.secao_id == Secao.id, isouter=True
        ).group_by(
            Recurso.id, Recurso.nome, Equipe.nome, Secao.nome
        )
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
            
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
            
        if projeto_id:
            query = query.filter(Apontamento.projeto_id == projeto_id)
            
        if equipe_id:
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
        if secao_id:
            query = query.filter(Equipe.secao_id == secao_id)
        
        import logging
        try:
            result = await self.db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "recurso_id": row.recurso_id,
                    "recurso_nome": row.recurso_nome,
                    "equipe_nome": row.equipe_nome,
                    "secao_nome": row.secao_nome,
                    "total_horas": float(row.total_horas) if row.total_horas else 0
                }
                for row in rows
            ]
        except Exception as e:
            logging.exception("Erro ao executar query de horas por recurso")
            raise
    
    async def get_analise_planejado_vs_realizado(
        self,
        ano: int,
        mes: Optional[int] = None,
        projeto_id: Optional[int] = None,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém análise comparativa entre horas planejadas e horas efetivamente apontadas.
        """
        # CTE para Horas Planejadas
        planejado_cte_query = select(
            AlocacaoRecursoProjeto.recurso_id,
            AlocacaoRecursoProjeto.projeto_id,
            HorasPlanejadas.ano,
            HorasPlanejadas.mes,
            func.sum(HorasPlanejadas.horas_planejadas).label("horas_planejadas")
        ).join(
            HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).filter(HorasPlanejadas.ano == ano)

        if mes:
            planejado_cte_query = planejado_cte_query.filter(HorasPlanejadas.mes == mes)
        if projeto_id:
            planejado_cte_query = planejado_cte_query.filter(AlocacaoRecursoProjeto.projeto_id == projeto_id)
        if recurso_id:
            planejado_cte_query = planejado_cte_query.filter(AlocacaoRecursoProjeto.recurso_id == recurso_id)

        if equipe_id or secao_id:
            planejado_cte_query = planejado_cte_query.join(Recurso, AlocacaoRecursoProjeto.recurso_id == Recurso.id)
            if equipe_id:
                planejado_cte_query = planejado_cte_query.filter(Recurso.equipe_principal_id == equipe_id)
            if secao_id:
                planejado_cte_query = planejado_cte_query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                planejado_cte_query = planejado_cte_query.filter(Equipe.secao_id == secao_id)

        planejado_cte_query = planejado_cte_query.group_by(
            AlocacaoRecursoProjeto.recurso_id,
            AlocacaoRecursoProjeto.projeto_id,
            HorasPlanejadas.ano,
            HorasPlanejadas.mes
        ).cte("planejado_cte")

        # CTE para Horas Realizadas (Apontadas)
        realizado_cte_query = select(
            Apontamento.recurso_id,
            Apontamento.projeto_id,
            extract("year", Apontamento.data_apontamento).label("ano"),
            extract("month", Apontamento.data_apontamento).label("mes"),
            func.sum(Apontamento.horas_apontadas).label("horas_realizadas")
        ).filter(extract("year", Apontamento.data_apontamento) == ano)

        if mes:
            realizado_cte_query = realizado_cte_query.filter(extract("month", Apontamento.data_apontamento) == mes)
        if projeto_id:
            realizado_cte_query = realizado_cte_query.filter(Apontamento.projeto_id == projeto_id)
        if recurso_id:
            realizado_cte_query = realizado_cte_query.filter(Apontamento.recurso_id == recurso_id)

        if equipe_id or secao_id:
            realizado_cte_query = realizado_cte_query.join(Recurso, Apontamento.recurso_id == Recurso.id)
            if equipe_id:
                realizado_cte_query = realizado_cte_query.filter(Recurso.equipe_principal_id == equipe_id)
            if secao_id:
                realizado_cte_query = realizado_cte_query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                realizado_cte_query = realizado_cte_query.filter(Equipe.secao_id == secao_id)

        realizado_cte_query = realizado_cte_query.group_by(
            Apontamento.recurso_id,
            Apontamento.projeto_id,
            extract("year", Apontamento.data_apontamento),
            extract("month", Apontamento.data_apontamento)
        ).cte("realizado_cte")

        # Consulta principal com FULL OUTER JOIN
        final_query = select(
            Recurso.id.label("recurso_id"),
            Recurso.nome.label("recurso_nome"),
            Projeto.id.label("projeto_id"),
            Projeto.nome.label("projeto_nome"),
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome"),
            func.coalesce(planejado_cte_query.c.ano, realizado_cte_query.c.ano).label("ano"),
            func.coalesce(planejado_cte_query.c.mes, realizado_cte_query.c.mes).label("mes"),
            func.coalesce(planejado_cte_query.c.horas_planejadas, 0).label("horas_planejadas"),
            func.coalesce(realizado_cte_query.c.horas_realizadas, 0).label("horas_realizadas")
        ).select_from(
            join(
                planejado_cte_query,
                realizado_cte_query,
                and_(
                    planejado_cte_query.c.recurso_id == realizado_cte_query.c.recurso_id,
                    planejado_cte_query.c.projeto_id == realizado_cte_query.c.projeto_id,
                    planejado_cte_query.c.ano == realizado_cte_query.c.ano,
                    planejado_cte_query.c.mes == realizado_cte_query.c.mes,
                ),
                full=True
            )
        ).join(
            Recurso, Recurso.id == func.coalesce(planejado_cte_query.c.recurso_id, realizado_cte_query.c.recurso_id)
        ).join(
            Projeto, Projeto.id == func.coalesce(planejado_cte_query.c.projeto_id, realizado_cte_query.c.projeto_id)
        ).join(
            Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True
        ).join(
            Secao, Equipe.secao_id == Secao.id, isouter=True
        )


        result = await self.db.execute(final_query)
        rows = result.mappings().all()

        response_data = []
        for row in rows:
            planejadas = float(row["horas_planejadas"])
            realizadas = float(row["horas_realizadas"])
            diferenca = planejadas - realizadas
            percentual = (realizadas / planejadas * 100) if planejadas > 0 else 0
            
            response_data.append({
                **row,
                "horas_planejadas": planejadas,
                "horas_realizadas": realizadas,
                "diferenca": diferenca,
                "percentual_realizado": round(percentual, 2)
            })
            
        return response_data
    
    async def get_disponibilidade_recursos(
        self,
        ano: int,
        mes: Optional[int] = None,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula e retorna a disponibilidade dos recursos, incluindo horas disponíveis,
        planejadas, realizadas, e métricas de utilização.

        Args:
            ano: Ano de referência.
            mes: Mês de referência (opcional, se não fornecido, retorna para o ano todo).
            recurso_id: ID do recurso específico (opcional).

        Returns:
            Lista de dicionários com os dados de disponibilidade por recurso e mês.
        """
        # Subconsulta para agregar horas planejadas por recurso, ano e mês
        subquery_planejadas = (
            select(
                AlocacaoRecursoProjeto.recurso_id,
                HorasPlanejadas.ano,
                HorasPlanejadas.mes,
                func.sum(HorasPlanejadas.horas_planejadas).label("total_horas_planejadas")
            )
            .join(HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id)
            .group_by(AlocacaoRecursoProjeto.recurso_id, HorasPlanejadas.ano, HorasPlanejadas.mes)
            .filter(HorasPlanejadas.ano == ano)
        )
        if mes:
            subquery_planejadas = subquery_planejadas.filter(HorasPlanejadas.mes == mes)
        if recurso_id:
            subquery_planejadas = subquery_planejadas.filter(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        subquery_planejadas = subquery_planejadas.cte("planejadas_cte")

        # Subconsulta para agregar horas apontadas por recurso, ano e mês
        subquery_apontadas = (
            select(
                Apontamento.recurso_id,
                extract("year", Apontamento.data_apontamento).label("ano"),
                extract("month", Apontamento.data_apontamento).label("mes"),
                func.sum(Apontamento.horas_apontadas).label("total_horas_realizadas")
            )
            .group_by(Apontamento.recurso_id, extract("year", Apontamento.data_apontamento), extract("month", Apontamento.data_apontamento))
            .filter(extract("year", Apontamento.data_apontamento) == ano)
        )
        if mes:
            subquery_apontadas = subquery_apontadas.filter(extract("month", Apontamento.data_apontamento) == mes)
        if recurso_id:
            subquery_apontadas = subquery_apontadas.filter(Apontamento.recurso_id == recurso_id)
        subquery_apontadas = subquery_apontadas.cte("apontadas_cte")

        # Consulta principal
        query = (
            select(
                Recurso.id.label("recurso_id"),
                Recurso.nome.label("recurso_nome"),
                HorasDisponiveisRH.ano,
                HorasDisponiveisRH.mes,
                HorasDisponiveisRH.horas_disponiveis_mes,
                func.coalesce(subquery_planejadas.c.total_horas_planejadas, 0).label("total_horas_planejadas"),
                func.coalesce(subquery_apontadas.c.total_horas_realizadas, 0).label("total_horas_realizadas")
            )
            .join(Recurso, Recurso.id == HorasDisponiveisRH.recurso_id)
            .outerjoin(
                subquery_planejadas,
                and_(
                    subquery_planejadas.c.recurso_id == HorasDisponiveisRH.recurso_id,
                    subquery_planejadas.c.ano == HorasDisponiveisRH.ano,
                    subquery_planejadas.c.mes == HorasDisponiveisRH.mes
                )
            )
            .outerjoin(
                subquery_apontadas,
                and_(
                    subquery_apontadas.c.recurso_id == HorasDisponiveisRH.recurso_id,
                    subquery_apontadas.c.ano == HorasDisponiveisRH.ano,
                    subquery_apontadas.c.mes == HorasDisponiveisRH.mes
                )
            )
            .filter(HorasDisponiveisRH.ano == ano)
        )

        if mes:
            query = query.filter(HorasDisponiveisRH.mes == mes)
        if recurso_id:
            query = query.filter(HorasDisponiveisRH.recurso_id == recurso_id)

        query = query.order_by(Recurso.nome, HorasDisponiveisRH.mes)
        
        result = await self.db.execute(query)
        rows = result.fetchall()

        response_data = []
        for row in rows:
            horas_disponiveis = row.horas_disponiveis_mes if row.horas_disponiveis_mes else 0
            horas_planejadas = row.total_horas_planejadas if row.total_horas_planejadas else 0
            horas_realizadas = row.total_horas_realizadas if row.total_horas_realizadas else 0

            horas_livres = horas_disponiveis - horas_planejadas
            
            percentual_alocacao = (horas_planejadas / horas_disponiveis * 100) if horas_disponiveis > 0 else 0
            percentual_utilizacao_planejado = (horas_realizadas / horas_planejadas * 100) if horas_planejadas > 0 else 0
            percentual_utilizacao_disponivel = (horas_realizadas / horas_disponiveis * 100) if horas_disponiveis > 0 else 0

            response_data.append({
                "recurso_id": row.recurso_id,
                "recurso_nome": row.recurso_nome,
                "ano": row.ano,
                "mes": row.mes,
                "horas_disponiveis_rh": horas_disponiveis,
                "horas_planejadas": horas_planejadas,
                "horas_realizadas": horas_realizadas,
                "horas_livres": horas_livres,
                "percentual_alocacao_rh": round(percentual_alocacao, 2),
                "percentual_utilizacao_sobre_planejado": round(percentual_utilizacao_planejado, 2),
                "percentual_utilizacao_sobre_disponivel_rh": round(percentual_utilizacao_disponivel, 2)
            })
            
        return response_data