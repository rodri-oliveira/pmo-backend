import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timedelta

# Data inicial padrão para carga completa de worklogs
DEFAULT_START_DATE = datetime(2024, 8, 1)

from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.db.session import AsyncSessionLocal

async def carga_completa():
    """
    Executa a carga completa de worklogs do Jira desde 01/08/2024 até hoje.
    """
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        data_inicio = DEFAULT_START_DATE
        data_fim = datetime.now()
        print(f"[CARGA COMPLETA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
        resultado = await service.sincronizar_apontamentos(data_inicio=data_inicio, data_fim=data_fim)
        print("[CARGA COMPLETA RESULTADO]", resultado)

async def carga_personalizada(start_str: str, end_str: str):
    from datetime import datetime
    try:
        data_inicio = datetime.fromisoformat(start_str)
        data_fim = datetime.fromisoformat(end_str)
    except Exception as e:
        print(f"[ERRO DATA] Formato inválido: {e}")
        return
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        print(f"[CARGA PERSONALIZADA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
        resultado = await service.sincronizar_apontamentos(data_inicio=data_inicio, data_fim=data_fim)
        print("[RESULTADO PERSONALIZADO]", resultado)

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
        print(f"[ROTINA MENSAL] Iniciando de {data_inicio.date()} até {data_fim.date()}")
        resultado = await service.sincronizar_apontamentos(data_inicio=data_inicio, data_fim=data_fim)
        print("[ROTINA MENSAL RESULTADO]", resultado)

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
