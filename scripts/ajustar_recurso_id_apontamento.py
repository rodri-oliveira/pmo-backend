import csv
import asyncio
from app.db.session import get_async_db
from app.db.orm_models import Apontamento, Recurso
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Caminho do arquivo CSV com o mapeamento worklog_id -> jira_user_id
CSV_PATH = 'scripts/worklog_jira_map.csv'

def carregar_mapeamento():
    mapping = {}
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            mapping[row['jira_worklog_id']] = row['jira_user_id']
    return mapping

async def corrigir_recurso_id():
    mapping = carregar_mapeamento()
    async for db in get_async_db():
        apontamentos = (await db.execute(select(Apontamento))).scalars().all()
        count = 0
        for apontamento in apontamentos:
            jira_user_id = mapping.get(str(apontamento.jira_worklog_id))
            if not jira_user_id:
                continue
            recurso = (await db.execute(select(Recurso).where(Recurso.jira_user_id == jira_user_id))).scalar_one_or_none()
            if recurso and apontamento.recurso_id != recurso.id:
                apontamento.recurso_id = recurso.id
                count += 1
                print(f"Apontamento {apontamento.id}: recurso_id corrigido para {recurso.id}")
        await db.commit()
        print(f"Correção concluída. {count} apontamentos atualizados.")

if __name__ == "__main__":
    asyncio.run(corrigir_recurso_id())
