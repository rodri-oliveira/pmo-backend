#!/usr/bin/env python3
"""
Script de teste para identificar problemas na importação do CSV.
"""

import sys
import os
import pandas as pd
import chardet
import re

# Garantir que o diretório raiz do projeto esteja no sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def testar_leitura_csv():
    """Testa a leitura do CSV e identifica problemas."""
    arquivo = "scripts/excel/SGI Cloud & DevOps.csv"
    arquivo_completo = os.path.join(PROJECT_ROOT, arquivo)
    
    print(f"Testando arquivo: {arquivo_completo}")
    print(f"Arquivo existe: {os.path.exists(arquivo_completo)}")
    
    if not os.path.exists(arquivo_completo):
        print("ERRO: Arquivo não encontrado!")
        return
    
    # Detectar encoding
    try:
        with open(arquivo_completo, 'rb') as f:
            enc_info = chardet.detect(f.read(4096))
            encoding_detected = enc_info.get('encoding') or 'utf-8'
        print(f"Encoding detectado: {encoding_detected}")
    except Exception as e:
        print(f"Erro ao detectar encoding: {e}")
        encoding_detected = 'utf-8'
    
    # Ler CSV
    try:
        df = pd.read_csv(
            arquivo_completo,
            sep=';',
            encoding=encoding_detected,
            decimal=',',
            skip_blank_lines=True
        )
        print(f"CSV lido com sucesso. Linhas: {len(df)}, Colunas: {len(df.columns)}")
        print(f"Primeiras 5 colunas: {list(df.columns[:5])}")
        print(f"Últimas 5 colunas: {list(df.columns[-5:])}")
        
        # Identificar colunas de horas
        padrao_mes = re.compile(r'^[a-zA-Z]{3}/\d{2}$')
        colunas_horas = [c for c in df.columns if padrao_mes.match(str(c).strip())]
        print(f"Colunas de horas encontradas: {colunas_horas}")
        
        # Verificar célula A6 (nome da equipe)
        if len(df) > 5:
            nome_equipe = str(df.iloc[5, 0]).strip()
            print(f"Nome da equipe (A6): '{nome_equipe}'")
        else:
            print("ERRO: Planilha não possui linha A6")
        
        # Verificar primeiros projetos (a partir da linha 7)
        print("\nPrimeiros projetos encontrados:")
        for index, linha in df.iterrows():
            if index >= 6 and index < 10:  # Linhas 7-10
                nome_projeto = str(linha.iloc[0]).strip()
                if nome_projeto and nome_projeto not in ['', 'nan', 'NaN']:
                    print(f"  Linha {index+1}: '{nome_projeto}'")
        
        return True
        
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return False

def testar_conexao_banco():
    """Testa conexão com o banco."""
    try:
        from app.db.session import get_sync_db
        from app.db.orm_models import Recurso
        
        session = next(get_sync_db())
        print("Conexão com banco estabelecida com sucesso")
        
        # Buscar recurso "João Vitor"
        recurso = session.query(Recurso).filter(
            Recurso.nome.ilike("%João Vitor%")
        ).first()
        
        if recurso:
            print(f"Recurso encontrado: {recurso.nome} (ID: {recurso.id})")
        else:
            print("ERRO: Recurso 'João Vitor' não encontrado no banco")
            # Listar alguns recursos para debug
            recursos = session.query(Recurso).limit(5).all()
            print("Primeiros 5 recursos no banco:")
            for r in recursos:
                print(f"  - {r.nome} (ID: {r.id})")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"Erro ao conectar com banco: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTE DE IMPORTAÇÃO CSV ===")
    print()
    
    print("1. Testando leitura do CSV...")
    csv_ok = testar_leitura_csv()
    print()
    
    print("2. Testando conexão com banco...")
    banco_ok = testar_conexao_banco()
    print()
    
    if csv_ok and banco_ok:
        print("✓ Todos os testes passaram. O problema pode estar na lógica de negócio.")
    else:
        print("✗ Alguns testes falharam. Verifique os erros acima.")
