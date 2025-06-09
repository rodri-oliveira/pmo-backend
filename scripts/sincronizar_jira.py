import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timedelta

# Data inicial padrão para carga completa de worklogs
DEFAULT_START_DATE = datetime(2024, 8, 1)

from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository

async def processar_periodo(data_inicio: datetime, data_fim: datetime):
    """
    Processa worklogs do Jira de data_inicio até data_fim
    Filtra projetos SEG, SGI, DTIN e TIN e faz upsert de apontamentos
    """
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        repo = ApontamentoRepository(session)
        client = JiraClient()
        project_keys = ["SEG", "SGI", "DTIN", "TIN"]  # chave real de SGI
        project_counts = {key: 0 for key in project_keys}
        total_count = 0
        # Para cada projeto, buscar e processar worklogs no período
        for proj_key in project_keys:
            jql = f"project = {proj_key} AND worklogDate >= '{data_inicio.date()}' AND worklogDate <= '{data_fim.date()}'"
            print(f"[PROCESSAR_PERIODO] JQL {proj_key}: {jql}")
            issues = client.search_issues(jql, fields=["worklog","author","started","timeSpentSeconds","comment"], max_results=1000)
            for issue in issues:
                for wl in issue.get("fields", {}).get("worklog", {}).get("worklogs", []):
                    try:
                        data = await service._extrair_dados_worklog(wl)
                        if data:
                            await repo.sync_jira_apontamento(wl.get("id"), data)
                            total_count += 1
                            project_counts[proj_key] += 1
                    except Exception as ex:
                        print(f"[ERRO_WORKLOG] id={wl.get('id')} -> {ex}")
        print(f"[PROCESSAR_PERIODO] {total_count} apontamentos processados")
        # resumo de apontamentos por projeto
        for key, count in project_counts.items():
            print(f"[PROCESSAR_PERIODO] {key}: {count} apontamentos")

async def carga_completa():
    """
    Executa a carga completa de worklogs do Jira desde 01/08/2024 até hoje.
    """
    data_inicio = DEFAULT_START_DATE
    data_fim = datetime.now()
    print(f"[CARGA COMPLETA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def carga_personalizada(start_str: str, end_str: str):
    from datetime import datetime
    try:
        data_inicio = datetime.fromisoformat(start_str)
        data_fim = datetime.fromisoformat(end_str)
    except Exception as e:
        print(f"[ERRO DATA] Formato inválido: {e}")
        return
    print(f"[CARGA PERSONALIZADA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def rotina_mensal():
    """
    Executa a rotina mensal de sincronização do Jira (mês anterior ao mês corrente).
    """
    hoje = datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    data_inicio = primeiro_dia_mes_anterior
    data_fim = ultimo_dia_mes_anterior
    print(f"[ROTINA MENSAL] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

if __name__ == "__main__":
    import sys
    # uso: python sincronizar_jira.py <start> <end> | mensal | (sem args)
    if len(sys.argv) == 3:
        _, start_str, end_str = sys.argv
        asyncio.run(carga_personalizada(start_str, end_str))
    elif len(sys.argv) > 1 and sys.argv[1] == "mensal":
        asyncio.run(rotina_mensal())
    else:
        asyncio.run(carga_completa())
