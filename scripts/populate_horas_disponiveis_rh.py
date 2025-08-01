import asyncio
import logging
import os
import sys
import io
from datetime import datetime

import pandas as pd
import psycopg2

# Adiciona o diretório raiz do projeto ao sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from app.core.config import settings

def populate_horas_disponiveis_rh():
    """Popula a tabela usando psycopg2 diretamente para máxima confiabilidade."""
    JORNADA_HORAS = 8
    conn = None
    
    try:
        # 1. Conectar diretamente com psycopg2
        logging.info("Conectando ao banco de dados com psycopg2...")
        conn = psycopg2.connect(
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT
        )
        cur = conn.cursor()
        logging.info("Conexão estabelecida com sucesso.")

        # 2. Buscar dados necessários
        logging.info("Buscando dias úteis e recursos ativos...")
        query_dias_uteis = "SELECT ano, mes, COUNT(data) as dias_uteis FROM dim_tempo WHERE is_dia_util = true GROUP BY ano, mes"
        df_dias_uteis = pd.read_sql(query_dias_uteis, conn)

        cur.execute("SELECT id FROM recurso WHERE ativo = true")
        recursos = [row[0] for row in cur.fetchall()]
        logging.info("Encontrados %d meses com dias úteis e %d recursos ativos.", len(df_dias_uteis), len(recursos))

        # 3. Preparar o DataFrame para inserção
        horas_data = []
        for recurso_id in recursos:
            for _, row in df_dias_uteis.iterrows():
                mes = row['mes']
                dias_uteis = row['dias_uteis']
                
                # AJUSTE: Férias forçadas - Saída 23/dez, volta 04/jan
                # Dezembro: excluir dias úteis de 23/dez em diante
                # Janeiro: excluir dias úteis até 03/jan
                if mes == 12:  # Dezembro
                    # Estimar que aproximadamente 7 dias úteis são perdidos (23-31 dez)
                    dias_ferias_dez = 7
                    dias_uteis_ajustados = max(0, dias_uteis - dias_ferias_dez)
                    horas_mes = dias_uteis_ajustados * JORNADA_HORAS
                    logging.info(f"Dezembro: Férias 23/dez-31/dez - {dias_uteis} dias -> {dias_uteis_ajustados} dias úteis -> {horas_mes}h")
                elif mes == 1:  # Janeiro
                    # Estimar que aproximadamente 3 dias úteis são perdidos (01-03 jan)
                    dias_ferias_jan = 3
                    dias_uteis_ajustados = max(0, dias_uteis - dias_ferias_jan)
                    horas_mes = dias_uteis_ajustados * JORNADA_HORAS
                    logging.info(f"Janeiro: Férias 01/jan-03/jan - {dias_uteis} dias -> {dias_uteis_ajustados} dias úteis -> {horas_mes}h")
                else:
                    horas_mes = dias_uteis * JORNADA_HORAS  # Horas normais
                
                horas_data.append({
                    'recurso_id': recurso_id,
                    'ano': row['ano'],
                    'mes': mes,
                    'horas_disponiveis_mes': horas_mes
                })
        df_horas = pd.DataFrame(horas_data)
        
        # Adiciona colunas de timestamp para satisfazer as constraints NOT NULL da tabela
        # CORREÇÃO: Usar 'data_atualizacao' em vez de 'data_modificacao'
        now = datetime.now()
        df_horas['data_criacao'] = now
        df_horas['data_atualizacao'] = now

        logging.info("Preparados %d registros para inserção.", len(df_horas))

        # 4. Limpar a tabela
        logging.info("Limpando a tabela 'horas_disponiveis_rh'...")
        cur.execute("TRUNCATE TABLE horas_disponiveis_rh RESTART IDENTITY")

        # 5. Inserir dados usando copy_from para alta performance
        if not df_horas.empty:
            logging.info("Iniciando inserção em massa...")
            buffer = io.StringIO()
            df_horas.to_csv(buffer, index=False, header=False)
            buffer.seek(0)
            cur.copy_from(buffer, 'horas_disponiveis_rh', sep=',', columns=df_horas.columns)
            logging.info("Inserção em massa concluída.")
        else:
            logging.warning("Nenhum dado para inserir.")

        # 6. Commit da transação
        conn.commit()
        logging.info("Transação commitada com sucesso! Dados persistidos.")

    except Exception as e:
        logging.error("Ocorreu um erro. Executando rollback: %s", e, exc_info=True)
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logging.info("Conexão com o banco de dados fechada.")

def main():
    """Configura o logging e executa o script."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', f'populate_horas_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)]
    )

    print(f"--- CONECTANDO AO BANCO: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME} ---")
    logging.info("=========================================================")
    logging.info("== Script para Popular a Tabela de Horas Disponíveis ==")
    logging.info("==              (horas_disponiveis_rh)               ==")
    logging.info("=========================================================")
    
    try:
        populate_horas_disponiveis_rh()
    except Exception:
        logging.error("A execução do script falhou. Verifique o log para detalhes.")

if __name__ == "__main__":
    main()