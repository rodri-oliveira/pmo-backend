#!/usr/bin/env python3
"""
Script para debugar valores da coluna F no CSV.
"""

import pandas as pd
import chardet
import os

def debug_coluna_f():
    """Debug específico da coluna F."""
    arquivo = "scripts/excel/SGI Cloud & DevOps.csv"
    arquivo_completo = os.path.join(os.path.dirname(os.path.dirname(__file__)), arquivo)
    
    print(f"Debugando arquivo: {arquivo_completo}")
    
    # Detectar encoding
    with open(arquivo_completo, 'rb') as f:
        enc_info = chardet.detect(f.read(4096))
        encoding_detected = enc_info.get('encoding') or 'utf-8'
    print(f"Encoding detectado: {encoding_detected}")
    
    # Ler CSV
    df = pd.read_csv(
        arquivo_completo,
        sep=';',
        encoding=encoding_detected,
        decimal=',',
        skip_blank_lines=True
    )
    
    print(f"CSV lido. Linhas: {len(df)}, Colunas: {len(df.columns)}")
    print(f"Nomes das colunas: {list(df.columns)}")
    print()
    
    # Verificar coluna F (índice 5)
    if len(df.columns) > 5:
        print("=== VALORES DA COLUNA F ===")
        coluna_f = df.columns[5]
        print(f"Nome da coluna F (índice 5): '{coluna_f}'")
        print()
        
        # Mostrar valores da coluna F para as primeiras 15 linhas
        for i in range(min(15, len(df))):
            valor = df.iloc[i, 5]
            valor_str = str(valor).strip()
            print(f"Linha {i+1} (índice {i}): '{valor}' → str: '{valor_str}' → tipo: {type(valor)}")
        
        print()
        print("=== FOCO NAS LINHAS DE PROJETOS (7+) ===")
        for i in range(6, min(15, len(df))):  # A partir da linha 7 (índice 6)
            valor = df.iloc[i, 5]
            valor_str = str(valor).strip()
            nome_projeto = str(df.iloc[i, 0]).strip()
            print(f"Linha {i+1}: Projeto='{nome_projeto}' | Esforço='{valor}' ('{valor_str}')")
    else:
        print("ERRO: CSV não tem coluna F (índice 5)")

if __name__ == "__main__":
    debug_coluna_f()
