import asyncio
import os
import sys
import pandas as pd
from sqlalchemy import text, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# --- Configurações ---
JORNADA_HORAS = 8

# Adiciona o diretório raiz do projeto ao path para permitir importações da app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from app.core.config import settings
from app.infrastructure.database.recurso_sql_model import RecursoSQL

async def get_db_session() -> AsyncSession:
    """Cria e retorna uma sessão assíncrona com o banco de dados."""
    engine = create_async_engine(settings.DATABASE_URI, echo=False)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return AsyncSessionLocal()

async def populate_horas_disponiveis_rh():
    """Popula a tabela horas_disponiveis_rh com base nos dias úteis da dim_tempo e nos recursos ativos."""
    print("Iniciando a população da tabela 'horas_disponiveis_rh'.")
    
    session = await get_db_session()
    sync_engine = create_engine(settings.DATABASE_URI.replace("+asyncpg", ""), echo=False)

    try:
        # 1. Buscar dias úteis da dim_tempo
        print("Buscando dias úteis da tabela dim_tempo...")
        query_dias_uteis = "SELECT ano, mes, COUNT(data) as dias_uteis FROM dim_tempo WHERE is_dia_util = true GROUP BY ano, mes"
        df_dias_uteis = pd.read_sql(query_dias_uteis, sync_engine)
        print(f"{len(df_dias_uteis)} registros de mês/ano com dias úteis encontrados.")

        # 2. Buscar recursos ativos
        print("Buscando recursos ativos...")
        query_recursos = select(RecursoSQL).where(RecursoSQL.ativo == True)
        result = await session.execute(query_recursos)
        recursos = result.scalars().all()
        if not recursos:
            print("Nenhum recurso ativo encontrado. Encerrando o script.")
            return
        print(f"{len(recursos)} recursos ativos encontrados.")

        # 3. Calcular horas disponíveis e preparar dados para inserção
        horas_disponiveis_data = []
        for recurso in recursos:
            for _, row in df_dias_uteis.iterrows():
                horas_disponiveis_data.append({
                    'recurso_id': recurso.id,
                    'ano': row['ano'],
                    'mes': row['mes'],
                    'horas_disponiveis_mes': row['dias_uteis'] * JORNADA_HORAS
                })
        
        if not horas_disponiveis_data:
            print("Nenhum dado de horas disponíveis para inserir. Encerrando.")
            return

        df_horas = pd.DataFrame(horas_disponiveis_data)

        # 4. Limpar dados existentes e inserir novos dados
        async with session.begin():
            print("Limpando dados existentes na tabela horas_disponiveis_rh...")
            await session.execute(text("TRUNCATE TABLE horas_disponiveis_rh RESTART IDENTITY"))

        print(f"Inserindo {len(df_horas)} registros na tabela horas_disponiveis_rh...")
        df_horas.to_sql('horas_disponiveis_rh', sync_engine, if_exists='append', index=False, method='multi')
        print("Inserção concluída com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante a operação com o banco de dados: {e}")
    finally:
        await session.close()
        sync_engine.dispose()
        print("Sessão com o banco de dados fechada.")

if __name__ == "__main__":
    print("=========================================================")
    print("== Script para Popular a Tabela de Horas Disponíveis ==")
    print("==              (horas_disponiveis_rh)               ==")
    print("=========================================================")
    asyncio.run(populate_horas_disponiveis_rh())
