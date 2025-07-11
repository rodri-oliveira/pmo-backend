"""
Script para comparar schema do banco com os modelos SQLAlchemy.
Usa reflection para obter tabelas e colunas do BD e compara com Base.metadata.
"""
import pkgutil
from sqlalchemy import create_engine, inspect
from app.infrastructure.database.database_config import DATABASE_URL, Base

# Importar todos os models SQL para popular Base.metadata
import app.infrastructure.database.projeto_sql_model
import app.infrastructure.database.recurso_sql_model
import app.infrastructure.database.secao_sql_model
import app.infrastructure.database.status_projeto_sql_model
import app.infrastructure.database.equipe_sql_model
import app.infrastructure.database.item_sql_model


def main():
    # Use synchronous driver URL by stripping async driver if present
    sync_url = DATABASE_URL
    if '+asyncpg' in sync_url:
        sync_url = sync_url.replace('+asyncpg', '')
    engine = create_engine(sync_url)
    inspector = inspect(engine)

    db_tables = set(inspector.get_table_names())
    model_tables = set(Base.metadata.tables.keys())

    all_tables = sorted(db_tables | model_tables)
    print(f"Total tabelas BD: {len(db_tables)}, Modelos: {len(model_tables)}\n")

    for table in all_tables:
        print(f"Tabela: {table}")
        db_cols = {col['name'] for col in inspector.get_columns(table)} if table in db_tables else set()
        model_cols = {col.name for col in Base.metadata.tables.get(table, {}).columns} if table in model_tables else set()

        cols_all = sorted(db_cols | model_cols)
        for col in cols_all:
            status = []
            status.append('DB' if col in db_cols else '   ')
            status.append('MODEL' if col in model_cols else '     ')
            print(f"  {col:30} {' '.join(status)}")
        print()


if __name__ == '__main__':
    main()
