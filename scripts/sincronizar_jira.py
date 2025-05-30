import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timedelta
from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.db.session import AsyncSessionLocal

async def carga_completa():
    """
    Executa a carga completa de worklogs do Jira desde 01/08/2024 até hoje.
    """
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        data_inicio = datetime(2024, 8, 1)
        data_fim = datetime.now()
        resultado = await service.sincronizar_apontamentos(data_inicio=data_inicio, data_fim=data_fim)
        print("[CARGA COMPLETA]", resultado)

async def rotina_mensal():
    """
    Executa a rotina mensal de sincronização do Jira (mês anterior ao mês corrente).
    """
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        hoje = datetime.now()
        primeiro_dia_mes_atual = hoje.replace(day=1)
        ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
        primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
        data_inicio = primeiro_dia_mes_anterior
        data_fim = ultimo_dia_mes_anterior
        resultado = await service.sincronizar_apontamentos(data_inicio=data_inicio, data_fim=data_fim)
        print("[ROTINA MENSAL]", resultado)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "mensal":
        asyncio.run(rotina_mensal())
    else:
        asyncio.run(carga_completa())
