from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete

from app.domain.models.status_projeto_model import StatusProjeto as DomainStatusProjeto
from app.application.dtos.status_projeto_dtos import StatusProjetoCreateDTO, StatusProjetoUpdateDTO
from app.domain.repositories.status_projeto_repository import StatusProjetoRepository
from app.infrastructure.database.status_projeto_sql_model import StatusProjetoSQL

class SQLAlchemyStatusProjetoRepository(StatusProjetoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, status_id: int) -> Optional[DomainStatusProjeto]:
        result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.id == status_id))
        status_sql = result.scalars().first()
        if status_sql:
            return DomainStatusProjeto.model_validate(status_sql)
        return None

    async def get_by_nome(self, nome: str) -> Optional[DomainStatusProjeto]:
        result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.nome == nome))
        status_sql = result.scalars().first()
        if status_sql:
            return DomainStatusProjeto.model_validate(status_sql)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[DomainStatusProjeto]:
        query = select(StatusProjetoSQL).order_by(StatusProjetoSQL.ordem_exibicao, StatusProjetoSQL.nome).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        status_sql = result.scalars().all()
        return [DomainStatusProjeto.model_validate(s) for s in status_sql]

    async def create(self, status_create_dto: StatusProjetoCreateDTO) -> DomainStatusProjeto:
        new_status_sql = StatusProjetoSQL(**status_create_dto.model_dump())
        self.db_session.add(new_status_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_status_sql)
        return DomainStatusProjeto.model_validate(new_status_sql)

    async def update(self, status_id: int, status_update_dto: StatusProjetoUpdateDTO) -> Optional[DomainStatusProjeto]:
        status_sql = await self.db_session.get(StatusProjetoSQL, status_id)
        if not status_sql:
            return None

        update_data = status_update_dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(status_sql, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(status_sql)
        return DomainStatusProjeto.model_validate(status_sql)

    async def delete(self, status_id: int) -> Optional[DomainStatusProjeto]:
        status_to_delete_sql = await self.db_session.get(StatusProjetoSQL, status_id)
        if not status_to_delete_sql:
            return None
        
        status_domain = DomainStatusProjeto.model_validate(status_to_delete_sql)
        await self.db_session.delete(status_to_delete_sql)
        await self.db_session.commit()
        return status_domain

