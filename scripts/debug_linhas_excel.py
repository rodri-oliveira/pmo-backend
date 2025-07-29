#!/usr/bin/env python3
"""
Script para debugar a leitura das linhas do Excel
"""

import pandas as pd
import sys

def debug_excel_lines(arquivo_excel: str, nome_aba: str):
    """Debug das linhas do Excel."""
    
    # Ler planilha
    df = pd.read_excel(
        arquivo_excel,
        sheet_name=nome_aba,
        engine='openpyxl',
        keep_default_na=False,
        na_values=[],
        dtype=str
    )
    
    print(f"=== DEBUG LINHAS EXCEL ===")
    print(f"Arquivo: {arquivo_excel}")
    print(f"Aba: {nome_aba}")
    print(f"Total de linhas: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}")
    print()
    
    # Mostrar todas as linhas
    for index, linha in df.iterrows():
        nome_projeto = str(linha.iloc[0]).strip() if len(linha) > 0 else ''
        observacao = str(linha.iloc[1]).strip() if len(linha) > 1 else ''
        status = str(linha.iloc[2]).strip() if len(linha) > 2 else ''
        esforco = str(linha.iloc[5]).strip() if len(linha) > 5 else ''
        
        print(f"Linha {index + 1} (índice {index}):")
        print(f"  - Coluna A (Projeto): '{nome_projeto}'")
        print(f"  - Coluna B (Observação): '{observacao}'")
        print(f"  - Coluna C (Status): '{status}'")
        print(f"  - Coluna F (Esforço): '{esforco}'")
        print()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python debug_linhas_excel.py <arquivo_excel> <nome_aba>")
        sys.exit(1)
    
    arquivo_excel = sys.argv[1]
    nome_aba = sys.argv[2]
    
    debug_excel_lines(arquivo_excel, nome_aba)
