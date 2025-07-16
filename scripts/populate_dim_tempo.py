import asyncio
import os
import sys
from datetime import date

import holidays
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# --- Configurações ---
START_YEAR = 2020
END_YEAR = 2040
JORNADA_HORAS = 8

# Adiciona o diretório raiz do projeto ao path para permitir importações da app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from app.core.config import settings

# --- Nomes em Português ---
DIAS_SEMANA = {
    0: 'Segunda-feira',
    1: 'Terça-feira',
    2: 'Quarta-feira',
    3: 'Quinta-feira',
    4: 'Sexta-feira',
    5: 'Sábado',
    6: 'Domingo'
}

MESES_ANO = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro'
}

async def get_db_session() -> AsyncSession:
    """Cria e retorna uma sessão assíncrona com o banco de dados."""
    engine = create_async_engine(settings.DATABASE_URI, echo=False)
    AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return AsyncSessionLocal()

async def populate_dim_tempo():
    """Popula a tabela dim_tempo com datas, feriados e dias úteis."""
    print(f"Iniciando a população da tabela 'dim_tempo' para os anos de {START_YEAR} a {END_YEAR}.")

    # 1. Obter feriados públicos (Nacional, Estadual, Municipal)
    br_holidays = holidays.country_holidays('BR', subdiv='SC')

    # 2. Adicionar feriados/recessos específicos da empresa (EDITAR AQUI)
    feriados_empresa = {
        # Exemplo de Férias Coletivas em Janeiro de 2025
        date(2025, 1, 2): "Recesso Pós Ano Novo",
        date(2025, 1, 3): "Recesso Pós Ano Novo",
        date(2025, 1, 6): "Recesso Pós Ano Novo",
        date(2025, 1, 7): "Recesso Pós Ano Novo",

        # Adicione outros dias aqui conforme necessário
        # Ex: date(2025, 3, 3): "Emenda de Carnaval",
    }
    br_holidays.update(feriados_empresa)
    print(f"Total de {len(br_holidays)} feriados e recessos configurados.")

    # 2. Gerar o DataFrame com todas as datas no intervalo
    datas = pd.date_range(start=f'{START_YEAR}-01-01', end=f'{END_YEAR}-12-31', freq='D')
    df = pd.DataFrame(datas, columns=['data'])
    print(f"{len(df)} dias serão processados.")

    # 3. Extrair atributos da data
    df['data'] = pd.to_datetime(df['data'])
    df['ano'] = df['data'].dt.year
    df['mes'] = df['data'].dt.month
    df['dia'] = df['data'].dt.day
    df['trimestre'] = df['data'].dt.quarter
    df['dia_semana'] = df['data'].dt.dayofweek  # Segunda=0, Domingo=6
    df['nome_dia_semana'] = df['dia_semana'].map(DIAS_SEMANA)
    df['nome_mes'] = df['mes'].map(MESES_ANO)
    df['semana_ano'] = df['data'].dt.isocalendar().week

    # 4. Identificar feriados e dias úteis
    df['is_feriado'] = df['data'].apply(lambda x: x in br_holidays)
    df['nome_feriado'] = df['data'].apply(lambda x: br_holidays.get(x))
    df['is_dia_util'] = (df['dia_semana'] < 5) & (~df['is_feriado'])

    # 5. Ajustar o nome da coluna 'data' para corresponder ao banco de dados
    # O nome da coluna 'data' já corresponde ao do banco de dados.
    # Adicionar a coluna data_id (se o banco não for auto-increment)
    df.insert(0, 'data_id', range(1, 1 + len(df)))
    df['data_id'] = (df['data'].dt.year * 10000) + (df['data'].dt.month * 100) + (df['data'].dt.day)

    # Reordenar colunas para corresponder à tabela dim_tempo
    df = df[[
        'data_id', 'data', 'ano', 'mes', 'dia', 'trimestre', 'dia_semana',
        'nome_dia_semana', 'nome_mes', 'semana_ano', 'is_dia_util',
        'is_feriado', 'nome_feriado'
    ]]

    # 6. Conectar ao banco e inserir os dados
    session = await get_db_session()
    try:
        async with session.begin():
            print(f"Limpando dados existentes na dim_tempo para o intervalo de {START_YEAR} a {END_YEAR}...")
            await session.execute(text(f"DELETE FROM dim_tempo WHERE ano >= {START_YEAR} AND ano <= {END_YEAR}"))

        print(f"Inserindo {len(df)} registros na tabela dim_tempo...")
        # Usando to_sql do pandas para bulk insert (requer um engine síncrono para esta operação)
        from sqlalchemy import create_engine
        # Criamos um engine síncrono para o bulk insert do pandas, com echo=False para não poluir o console
        sync_engine = create_engine(settings.DATABASE_URI.replace("+asyncpg", ""), echo=False)
        df.to_sql('dim_tempo', sync_engine, if_exists='append', index=False, method='multi')
        print("Inserção concluída com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro durante a operação com o banco de dados: {e}")
    finally:
        await session.close()
        print("Sessão com o banco de dados fechada.")

if __name__ == "__main__":
    # Para executar este script, use o comando a partir do diretório raiz do projeto:
    # python -m app.scripts.populate_dim_tempo
    print("==================================================")
    print("==   Script para Popular a Tabela de Dimensão   ==")
    print("==                  (dim_tempo)                 ==")
    print("==================================================")
    asyncio.run(populate_dim_tempo())
