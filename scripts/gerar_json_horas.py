"""
Script para gerar JSONB de horas planejadas a partir de planilha Excel.
Gera uma lista de objetos com formato:
  {"recurso_id": int, "nome_projeto": str, "h": [h1..h12]}
Usado na função inserir_horas_planejadas_json.
"""
import pandas as pd
import json
from app.db.session import SessionLocal
from app.db.orm_models import Recurso

# Caminho para a planilha na pasta data/
EXCEL_PATH = r"c:\weg\automacaopmobackend\data\projetos.xlsx"
# Index da linha onde estão os cabeçalhos (0-indexed, 6 = linha 7 no Excel)
SHEET_HEADER_ROW = 6

def gerar_json():
    # Lê Excel com cabeçalhos na linha 7 e filtra só 'Em andamento'
    df = pd.read_excel(EXCEL_PATH, header=SHEET_HEADER_ROW)
    df = df[df['Status'] == 'Em andamento']
    # Colunas de meses de M (índice 12) até X (índice 23)
    month_cols = df.columns[12:24]
    lista = []
    # Conexão DB para mapear assignee->recurso
    session = SessionLocal()
    for _, row in df.iterrows():
        login = row.get('Assignee')
        recurso = session.query(Recurso).filter(
            Recurso.email.ilike(f"{login}@%")
        ).first()
        if not recurso:
            print(f"Aviso: assignee '{login}' sem recurso correspondente, pulando linha.")
            continue
        horas = [float(row[c]) if not pd.isna(row[c]) else 0.0 for c in month_cols]
        obj = {
            'recurso_id': recurso.id,
            'nome_projeto': row.get('EPIC'),
            'h': horas
        }
        lista.append(obj)
    session.close()
    print(json.dumps(lista, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    gerar_json()
