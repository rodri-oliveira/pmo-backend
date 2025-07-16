from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import select, func, case, and_, or_, cast, String, extract, literal, literal_column, union_all, Float, Date
from app.infrastructure.database.dim_tempo_sql_model import DimTempoSQL as DimTempo
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import (
    Apontamento, 
    Recurso, 
    Projeto, 
    Equipe, 
    Secao, 
    AlocacaoRecursoProjeto, 
    HorasPlanejadas,
    HorasDisponiveisRH,
    StatusProjeto
)
from app.models.schemas import HorasDisponiveisRequest, HorasDisponiveisResponse, MesHoras

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
            import logging
            logging.exception("Erro ao executar query de horas por recurso")
            raise

    # -------------------------------------------------------------------------
    # Relatório Planejado vs Realizado 2 (POST)
    # -------------------------------------------------------------------------
    async def _determinar_intervalo_datas(self, recurso_id: int, mes_inicio: Optional[str], mes_fim: Optional[str]):
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        from calendar import monthrange

        def parse_mes(m: Optional[str]) -> Optional[datetime]:
            if not m or m.lower() == 'string':
                return None
            try:
                return datetime.strptime(m, "%Y-%m")
            except ValueError:
                return None

        dt_inicio = parse_mes(mes_inicio)
        dt_fim = parse_mes(mes_fim)

        if not dt_inicio or not dt_fim:
            HP, ARP, AP = HorasPlanejadas, AlocacaoRecursoProjeto, Apontamento
            
            planned_dates_q = (
                select(func.min(func.to_date(HP.ano.cast(String) + '-' + HP.mes.cast(String), 'YYYY-MM')).label('min_date'),
                       func.max(func.to_date(HP.ano.cast(String) + '-' + HP.mes.cast(String), 'YYYY-MM')).label('max_date'))
                .join(ARP, ARP.id == HP.alocacao_id)
                .where(ARP.recurso_id == recurso_id)
            )
            
            realized_dates_q = (
                select(func.min(func.date_trunc('month', AP.data_apontamento)).cast(Date).label('min_date'),
                       func.max(func.date_trunc('month', AP.data_apontamento)).cast(Date).label('max_date'))
                .where(AP.recurso_id == recurso_id)
            )

            planned_result = await self.db.execute(planned_dates_q)
            planned_dates = planned_result.first()
            
            realized_result = await self.db.execute(realized_dates_q)
            realized_dates = realized_result.first()

            all_dates = []
            if planned_dates and planned_dates.min_date:
                all_dates.append(planned_dates.min_date)
            if planned_dates and planned_dates.max_date:
                all_dates.append(planned_dates.max_date)
            if realized_dates and realized_dates.min_date:
                all_dates.append(realized_dates.min_date)
            if realized_dates and realized_dates.max_date:
                all_dates.append(realized_dates.max_date)

            if not all_dates:
                today = datetime.today()
                dt_inicio = dt_inicio or today.replace(day=1)
                dt_fim = dt_fim or today
            else:
                min_db_date = min(all_dates)
                max_db_date = max(all_dates)
                dt_inicio = dt_inicio or min_db_date
                dt_fim = dt_fim or max_db_date
        
        if dt_fim:
            last_day = monthrange(dt_fim.year, dt_fim.month)[1]
            dt_fim = dt_fim.replace(day=last_day)

        meses_intervalo = []
        current_mes = dt_inicio
        while current_mes <= dt_fim:
            meses_intervalo.append(current_mes.strftime("%Y-%m"))
            current_mes += relativedelta(months=1)
            
        return dt_inicio, dt_fim, meses_intervalo

    async def _get_disponibilidade_recurso(self, recurso_id: int, dt_inicio: datetime, dt_fim: datetime) -> Dict[tuple, float]:
        query = (
            select(HorasDisponiveisRH.ano, HorasDisponiveisRH.mes, HorasDisponiveisRH.horas_disponiveis_mes)
            .where(HorasDisponiveisRH.recurso_id == recurso_id)
            .where(
                func.to_date(
                    HorasDisponiveisRH.ano.cast(String) + '-' + HorasDisponiveisRH.mes.cast(String), 
                    'YYYY-MM'
                ).between(dt_inicio, dt_fim)
            )
        )
        result = await self.db.execute(query)
        return {(row.ano, row.mes): row.horas_disponiveis_mes for row in result.fetchall()}

    async def get_planejado_vs_realizado_v2(
        self,
        recurso_id: int,
        status: Optional[str] = None,
        mes_inicio: Optional[str] = None,
        mes_fim: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. Determinar o intervalo de meses
        dt_inicio, dt_fim, meses_intervalo = await self._determinar_intervalo_datas(
            recurso_id, mes_inicio, mes_fim
        )

        # 2. Obter disponibilidade do recurso
        disponibilidade_mes = await self._get_disponibilidade_recurso(
            recurso_id, dt_inicio, dt_fim
        )

        # 3. Construir a consulta unificada para horas planejadas e realizadas
        HP, ARP, AP, P, S = HorasPlanejadas, AlocacaoRecursoProjeto, Apontamento, Projeto, StatusProjeto

        planned_q = (
            select(
                ARP.projeto_id,
                HP.ano,
                HP.mes,
                HP.horas_planejadas.label("planejado"),
                literal_column("0").cast(Float).label("realizado"),
            )
            .join(ARP, ARP.id == HP.alocacao_id)
            .where(ARP.recurso_id == recurso_id)
        )

        realized_q = (
            select(
                AP.projeto_id,
                extract("year", AP.data_apontamento).label("ano"),
                extract("month", AP.data_apontamento).label("mes"),
                literal_column("0").cast(Float).label("planejado"),
                func.sum(AP.horas_apontadas).label("realizado"),
            )
            .where(AP.recurso_id == recurso_id)
            .group_by(
                AP.projeto_id,
                extract("year", AP.data_apontamento),
                extract("month", AP.data_apontamento),
            )
        )

        unified_query = union_all(planned_q, realized_q).alias("unified_query")

        # Subconsulta para agregar as observações por projeto
        acao_subquery = (
            select(
                ARP.projeto_id,
                func.string_agg(ARP.observacao, '\n').label("acao")
            )
            .where(ARP.recurso_id == recurso_id)
            .where(ARP.observacao.isnot(None))
            .group_by(ARP.projeto_id)
            .alias("acao_subquery")
        )

        # Consulta principal agregada
        main_q = (
            select(
                unified_query.c.projeto_id,
                P.nome.label("projeto_nome"),
                P.codigo_empresa,
                S.nome.label("status_nome"),
                acao_subquery.c.acao,
                unified_query.c.ano,
                unified_query.c.mes,
                func.sum(unified_query.c.planejado).label("total_planejado"),
                func.sum(unified_query.c.realizado).label("total_realizado"),
            )
            .join(P, P.id == unified_query.c.projeto_id)
            .join(S, S.id == P.status_projeto_id, isouter=True)
            .join(
                acao_subquery,
                acao_subquery.c.projeto_id == unified_query.c.projeto_id,
                isouter=True,
            )
            .where(
                func.to_date(
                    unified_query.c.ano.cast(String)
                    + "-"
                    + unified_query.c.mes.cast(String),
                    "YYYY-MM",
                ).between(dt_inicio, dt_fim)
            )
            .group_by(
                unified_query.c.projeto_id,
                P.nome,
                P.codigo_empresa,
                S.nome,
                acao_subquery.c.acao,
                unified_query.c.ano,
                unified_query.c.mes,
            )
        )

        if status and status != "string":
            main_q = main_q.where(S.nome == status)

        result = await self.db.execute(main_q)
        rows = result.fetchall()

        acao_result = await self.db.execute(select(acao_subquery))
        acoes_map = {row.projeto_id: row.acao for row in acao_result}

        # 4. Processar resultados e montar estrutura de projetos
        projetos_map = {}
        for row in rows:
            projeto_id = row.projeto_id
            if projeto_id not in projetos_map:
                projetos_map[projeto_id] = {
                    "id": projeto_id,
                    "nome": row.projeto_nome,
                    "status": row.status_nome,
                    "acao": row.acao,
                    "esforco_estimado": None,  # AINDA PRECISA IMPLEMENTAR
                    "esforco_planejado": 0,
                    "meses": {
                        m: {"planejado": 0, "realizado": 0} for m in meses_intervalo
                    },
                }

            mes_str = f"{int(row.ano)}-{int(row.mes):02d}"
            if mes_str in projetos_map[projeto_id]["meses"]:
                projetos_map[projeto_id]["meses"][mes_str]["planejado"] = float(
                    row.total_planejado or 0
                )
                projetos_map[projeto_id]["meses"][mes_str]["realizado"] = float(
                    row.total_realizado or 0
                )

        for p_id, projeto in projetos_map.items():
            # Garante inclusão da observação (ação) agregada
            projeto["acao"] = acoes_map.get(p_id, projeto.get("acao") or "")
            # Calcula esforço total planejado
            projeto["esforco_planejado"] = sum(
                m["planejado"] for m in projeto["meses"].values()
            )

        # 5. Montar linhas de resumo
        resumo_gap = {"label": "GAP", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_disponivel = {"label": "Horas Disponíveis", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_total = {"label": "Total de esforço (hrs)", "meses": {m: {"planejado": 0, "realizado": 0} for m in meses_intervalo}}

        for mes_str in meses_intervalo:
            ano, mes = map(int, mes_str.split('-'))

            disp_mes = float(disponibilidade_mes.get((ano, mes), 0) or 0)
            total_plano_mes = sum(p["meses"][mes_str]["planejado"] for p in projetos_map.values())
            total_real_mes = sum(p["meses"][mes_str]["realizado"] for p in projetos_map.values())

            resumo_disponivel["meses"][mes_str]["planejado"] = disp_mes
            resumo_total["meses"][mes_str]["planejado"] = total_plano_mes
            resumo_total["meses"][mes_str]["realizado"] = total_real_mes
            resumo_gap["meses"][mes_str]["planejado"] = disp_mes - total_plano_mes

        final_list = list(projetos_map.values())
        final_list.append(resumo_gap)
        final_list.append(resumo_disponivel)
        final_list.append(resumo_total)

        for item in final_list:
            if isinstance(item, dict) and "meses" in item:
                for mes, valores in item["meses"].items():
                    if valores["planejado"] > 0:
                        item["percentual_realizado"] = round((valores["realizado"] / valores["planejado"]) * 100, 2)
                    else:
                        item["percentual_realizado"] = 100 if valores["realizado"] > 0 else 0

        return sorted(final_list, key=lambda x: (x.get('label', x.get('nome', ''))))

    async def get_disponibilidade_recursos(
        self,
        ano: int,
        mes: Optional[int] = None,
        recurso_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula a disponibilidade dos recursos (horas disponíveis, planejadas, realizadas e livres)
        para um determinado ano e, opcionalmente, para um mês específico.

        Args:
            ano (int): O ano para o qual a disponibilidade será calculada.
            mes (Optional[int]): O mês específico para filtrar os dados. Se None, calcula para o ano todo.
            recurso_id (Optional[int]): O ID de um recurso específico para filtrar os dados.

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

    async def get_horas_disponiveis_recurso(
        self,
        request: HorasDisponiveisRequest
    ) -> HorasDisponiveisResponse:
        """
        Busca as horas disponíveis para um recurso dentro de um período de meses.
        """
                # Detecta os campos corretos no request (compatibilidade)
        if hasattr(request, 'mes_inicio') and hasattr(request, 'mes_fim'):
            start_str = request.mes_inicio
            end_str = request.mes_fim
        else:
            start_str = request.data_inicio
            end_str = request.data_fim

        # Extrai o ano e mês de início e fim
        start_year, start_month = map(int, start_str.split('-'))
        end_year, end_month = map(int, end_str.split('-'))

        # Constrói a data de início e fim para a query
        start_date = date(start_year, start_month, 1)
        end_date = date(end_year, end_month, 1)

        # Subquery para buscar as horas disponíveis na tabela de RH
        rh_query = (
            select(
                HorasDisponiveisRH.mes,
                HorasDisponiveisRH.ano,
                HorasDisponiveisRH.horas_disponiveis_mes
            )
            .where(HorasDisponiveisRH.recurso_id == request.recurso_id)
            .where(
                func.to_date(HorasDisponiveisRH.ano.cast(String) + '-' + HorasDisponiveisRH.mes.cast(String), 'YYYY-MM')
                .between(start_date, end_date)
            )
            .alias("rh_query")
        )

        # Query principal para buscar os meses do período na dim_tempo
        # e juntar com as horas disponíveis
        # Constrói expressão 'YYYY-MM' a partir de ano e mês
        mes_ano_expr = func.concat(
            DimTempo.ano.cast(String),
            '-',
            func.lpad(DimTempo.mes.cast(String), 2, '0')
        ).label('mes_ano_str')

        main_query = (
            select(
                mes_ano_expr,
                func.coalesce(func.max(rh_query.c.horas_disponiveis_mes), 0).label("horas_disponiveis"),
                DimTempo.ano,
                DimTempo.mes
            )
            .select_from(DimTempo)
            .outerjoin(
                rh_query, 
                and_(
                    DimTempo.mes == rh_query.c.mes,
                    DimTempo.ano == rh_query.c.ano
                )
            )
            .where(
                func.to_date(mes_ano_expr, 'YYYY-MM')
                .between(start_date, end_date)
            )
            .distinct()
            .group_by(mes_ano_expr, DimTempo.ano, DimTempo.mes)
            .order_by(DimTempo.ano, DimTempo.mes)
        )

        result = await self.db.execute(main_query)
        rows = result.fetchall()

        meses_horas = [
            MesHoras(mes=row.mes_ano_str, horas=row.horas_disponiveis)
            for row in rows
        ]

        periodo_dict = {"data_inicio": start_str, "data_fim": end_str}

        return HorasDisponiveisResponse(
            recurso_id=request.recurso_id,
            periodo=periodo_dict,
            horas_por_mes=meses_horas
        )