from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import select, func, case, and_, or_, cast, String, Integer, extract, literal, literal_column, union_all, Float, Date
# Alterando a importação para o local correto
from app.db.orm_models import DimTempo
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
        status_id: Optional[int] = None,
        alocacao_id: Optional[int] = None,
        mes_inicio: Optional[str] = None,
        mes_fim: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Relatório Planejado vs Realizado 2 - VERSÃO OTIMIZADA.
        
        Otimizações implementadas:
        - Redução de queries de 5+ para 2 queries principais
        - Eliminação de loops N+1 
        - Uso de CTEs para melhor performance
        - Agregações feitas em SQL ao invés de Python
        """
        # 1. Determinar o intervalo de meses
        dt_inicio, dt_fim, meses_intervalo = await self._determinar_intervalo_datas(
            recurso_id, mes_inicio, mes_fim
        )

        # 2. Obter disponibilidade do recurso
        disponibilidade_mes = await self._get_disponibilidade_recurso(
            recurso_id, dt_inicio, dt_fim
        )

        # 3. QUERY OTIMIZADA ÚNICA - Busca todos os dados necessários em uma só consulta
        HP, ARP, AP, P, S = HorasPlanejadas, AlocacaoRecursoProjeto, Apontamento, Projeto, StatusProjeto

        # CTE para todas as alocações do recurso com informações básicas
        alocacoes_cte = (
            select(
                ARP.id.label("alocacao_id"),
                ARP.projeto_id,
                ARP.status_alocacao_id,
                ARP.esforco_estimado,
                ARP.observacao,
                P.nome.label("projeto_nome"),
                P.codigo_empresa,
                S.nome.label("status_nome")
            )
            .select_from(ARP)
            .join(P, P.id == ARP.projeto_id)
            .outerjoin(S, S.id == ARP.status_alocacao_id)
            .where(ARP.recurso_id == recurso_id)
        )
        
        # Aplicar filtros opcionais
        if alocacao_id:
            alocacoes_cte = alocacoes_cte.where(ARP.id == alocacao_id)
        if status_id:
            alocacoes_cte = alocacoes_cte.where(ARP.status_alocacao_id == status_id)
            
        alocacoes_cte = alocacoes_cte.cte("alocacoes_cte")

        # CTE para horas planejadas agregadas por projeto/mês
        horas_planejadas_cte = (
            select(
                alocacoes_cte.c.projeto_id,
                HP.ano,
                HP.mes,
                func.sum(HP.horas_planejadas).label("total_planejado")
            )
            .select_from(alocacoes_cte)
            .outerjoin(HP, HP.alocacao_id == alocacoes_cte.c.alocacao_id)
            .group_by(alocacoes_cte.c.projeto_id, HP.ano, HP.mes)
            .cte("horas_planejadas_cte")
        )

        # CTE para horas realizadas agregadas por projeto/mês
        horas_realizadas_cte = (
            select(
                AP.projeto_id,
                extract("year", AP.data_apontamento).label("ano"),
                extract("month", AP.data_apontamento).label("mes"),
                func.sum(AP.horas_apontadas).label("total_realizado")
            )
            .where(AP.recurso_id == recurso_id)
            .group_by(
                AP.projeto_id,
                extract("year", AP.data_apontamento),
                extract("month", AP.data_apontamento)
            )
            .cte("horas_realizadas_cte")
        )

        # CTE para observações agregadas por projeto
        observacoes_cte = (
            select(
                alocacoes_cte.c.projeto_id,
                func.string_agg(alocacoes_cte.c.observacao, '\n').label("acao")
            )
            .where(alocacoes_cte.c.observacao.isnot(None))
            .group_by(alocacoes_cte.c.projeto_id)
            .cte("observacoes_cte")
        )

        # Query principal otimizada que combina todos os dados
        main_query = (
            select(
                alocacoes_cte.c.projeto_id,
                alocacoes_cte.c.alocacao_id,
                alocacoes_cte.c.projeto_nome,
                alocacoes_cte.c.codigo_empresa,
                alocacoes_cte.c.status_nome,
                alocacoes_cte.c.esforco_estimado,
                func.coalesce(observacoes_cte.c.acao, '').label("acao"),
                func.coalesce(horas_planejadas_cte.c.ano, horas_realizadas_cte.c.ano).label("ano"),
                func.coalesce(horas_planejadas_cte.c.mes, horas_realizadas_cte.c.mes).label("mes"),
                func.coalesce(horas_planejadas_cte.c.total_planejado, 0).label("total_planejado"),
                func.coalesce(horas_realizadas_cte.c.total_realizado, 0).label("total_realizado")
            )
            .select_from(alocacoes_cte)
            .outerjoin(observacoes_cte, observacoes_cte.c.projeto_id == alocacoes_cte.c.projeto_id)
            .outerjoin(
                horas_planejadas_cte,
                horas_planejadas_cte.c.projeto_id == alocacoes_cte.c.projeto_id
            )
            .outerjoin(
                horas_realizadas_cte,
                and_(
                    horas_realizadas_cte.c.projeto_id == alocacoes_cte.c.projeto_id,
                    or_(
                        horas_planejadas_cte.c.ano.is_(None),
                        and_(
                            horas_realizadas_cte.c.ano == horas_planejadas_cte.c.ano,
                            horas_realizadas_cte.c.mes == horas_planejadas_cte.c.mes
                        )
                    )
                )
            )
            .where(
                or_(
                    and_(
                        horas_planejadas_cte.c.ano.isnot(None),
                        func.to_date(
                            horas_planejadas_cte.c.ano.cast(String) + "-" + horas_planejadas_cte.c.mes.cast(String),
                            "YYYY-MM"
                        ).between(dt_inicio, dt_fim)
                    ),
                    and_(
                        horas_realizadas_cte.c.ano.isnot(None),
                        func.to_date(
                            horas_realizadas_cte.c.ano.cast(String) + "-" + horas_realizadas_cte.c.mes.cast(String),
                            "YYYY-MM"
                        ).between(dt_inicio, dt_fim)
                    ),
                    and_(
                        horas_planejadas_cte.c.ano.is_(None),
                        horas_realizadas_cte.c.ano.is_(None)
                    )
                )
            )
        )

        # Executar query principal otimizada
        result = await self.db.execute(main_query)
        rows = result.fetchall()

        # 4. Processar resultados de forma otimizada
        projetos_map = {}
        
        for row in rows:
            projeto_id = row.projeto_id
            
            # Inicializar projeto se não existir
            if projeto_id not in projetos_map:
                projetos_map[projeto_id] = {
                    "id": projeto_id,
                    "nome": row.projeto_nome,
                    "status": row.status_nome or "",
                    "alocacao_id": row.alocacao_id,
                    "acao": row.acao or "",
                    "esforco_estimado": float(row.esforco_estimado) if row.esforco_estimado is not None else None,
                    "esforco_planejado": 0,
                    "meses": {
                        m: {"planejado": 0, "realizado": 0} for m in meses_intervalo
                    },
                }

            # Processar dados mensais se existirem
            if row.ano and row.mes:
                mes_str = f"{int(row.ano)}-{int(row.mes):02d}"
                if mes_str in projetos_map[projeto_id]["meses"]:
                    projetos_map[projeto_id]["meses"][mes_str]["planejado"] = float(row.total_planejado or 0)
                    projetos_map[projeto_id]["meses"][mes_str]["realizado"] = float(row.total_realizado or 0)

        # Calcular esforço total planejado para cada projeto
        for projeto in projetos_map.values():
            projeto["esforco_planejado"] = sum(
                m["planejado"] for m in projeto["meses"].values()
            )
        
        # 5. Montar linhas de resumo (otimizado)
        resumo_gap = {"label": "GAP", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_disponivel = {"label": "Horas Disponíveis", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_total = {"label": "Total de esforço (hrs)", "meses": {m: {"planejado": 0, "realizado": 0} for m in meses_intervalo}}

        # Calcular resumos de forma otimizada
        for mes_str in meses_intervalo:
            ano, mes = map(int, mes_str.split('-'))
            disp_mes = float(disponibilidade_mes.get((ano, mes), 0) or 0)
            
            # Somar totais usando compreensão de lista (mais eficiente)
            total_plano_mes = sum(p["meses"][mes_str]["planejado"] for p in projetos_map.values())
            total_real_mes = sum(p["meses"][mes_str]["realizado"] for p in projetos_map.values())

            resumo_disponivel["meses"][mes_str]["planejado"] = disp_mes
            resumo_total["meses"][mes_str]["planejado"] = total_plano_mes
            resumo_total["meses"][mes_str]["realizado"] = total_real_mes
            resumo_gap["meses"][mes_str]["planejado"] = disp_mes - total_plano_mes

        # Montar resultado final
        final_list = list(projetos_map.values())
        final_list.extend([resumo_gap, resumo_disponivel, resumo_total])

        # Calcular totais finais de forma otimizada
        for item in final_list:
            if "meses" in item:
                valores_meses = item["meses"].values()
                item["esforco_planejado"] = sum(v.get("planejado", 0) for v in valores_meses)
                item["esforco_realizado"] = sum(v.get("realizado", 0) or 0 for v in valores_meses)

        # Separar projetos das linhas de resumo para o retorno
        linhas_resumo = [item for item in final_list if "label" in item]
        projetos_formatados = [item for item in final_list if "id" in item]

        # Retornar resultado final otimizado no formato esperado pela API
        return {
            "linhas_resumo": sorted(linhas_resumo, key=lambda x: x.get('label', '')),
            "projetos": sorted(projetos_formatados, key=lambda x: x.get('nome', '')),
        }

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