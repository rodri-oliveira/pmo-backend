from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_, or_
import traceback # Adicionado para logging detalhado
from datetime import datetime
from app.domain.models.recurso_model import Recurso as DomainRecurso
from app.application.dtos.recurso_dtos import RecursoCreateDTO, RecursoUpdateDTO
from app.domain.repositories.recurso_repository import RecursoRepository
from app.infrastructure.database.recurso_sql_model import RecursoSQL

class SQLAlchemyRecursoRepository(RecursoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, recurso_id: int) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(RecursoSQL).filter(RecursoSQL.id == recurso_id))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_email(self, email: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(RecursoSQL).filter(RecursoSQL.email == email))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_matricula(self, matricula: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(RecursoSQL).filter(RecursoSQL.matricula == matricula))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_jira_user_id(self, jira_user_id: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(RecursoSQL).filter(RecursoSQL.jira_user_id == jira_user_id))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, equipe_id: Optional[int] = None) -> List[DomainRecurso]:
        query = select(RecursoSQL)
        if apenas_ativos:
            query = query.filter(RecursoSQL.ativo == True)
        if equipe_id is not None:
            query = query.filter(RecursoSQL.equipe_principal_id == equipe_id)
        
        query = query.offset(skip).limit(limit)
        
        try:
            result = await self.db_session.execute(query)
            recursos_sql = result.scalars().all()
            return [DomainRecurso.model_validate(recurso) for recurso in recursos_sql]
        except Exception as e:
            print(f"Erro ao executar query no get_all: {e}")
            traceback.print_exc()
            raise

    async def create(self, recurso_create_dto: RecursoCreateDTO) -> DomainRecurso:
        new_recurso_sql = RecursoSQL(
            **recurso_create_dto.model_dump(),
            data_criacao=datetime.utcnow(),
            data_atualizacao=datetime.utcnow(),
            ativo=True  # se necessário
        )
        self.db_session.add(new_recurso_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_recurso_sql)
        return DomainRecurso.model_validate(new_recurso_sql)

    async def update(self, recurso_id: int, recurso_update_dto: RecursoUpdateDTO) -> Optional[DomainRecurso]:
        recurso_sql = await self.db_session.get(RecursoSQL, recurso_id)
        if not recurso_sql:
            return None

        update_data = recurso_update_dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(recurso_sql, key, value)
        
        try:
            await self.db_session.commit()
            await self.db_session.refresh(recurso_sql)
            return DomainRecurso.model_validate(recurso_sql)
        except Exception as e:
            await self.db_session.rollback()
            print(f"Error updating recurso: {e}")
            traceback.print_exc()
            return None

    async def delete(self, recurso_id: int) -> Optional[DomainRecurso]:
        recurso_to_delete_sql = await self.db_session.get(RecursoSQL, recurso_id)
        if not recurso_to_delete_sql:
            return None
        
        recurso_domain = DomainRecurso.model_validate(recurso_to_delete_sql)
        await self.db_session.delete(recurso_to_delete_sql)
        await self.db_session.commit()
        return recurso_domain
