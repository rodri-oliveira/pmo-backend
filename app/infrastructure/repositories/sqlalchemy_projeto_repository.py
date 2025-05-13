from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_

from app.domain.models.projeto_model import Projeto as DomainProjeto
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO
from app.domain.repositories.projeto_repository import ProjetoRepository
from app.infrastructure.database.projeto_sql_model import ProjetoSQL

class SQLAlchemyProjetoRepository(ProjetoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, projeto_id: int) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(ProjetoSQL).filter(ProjetoSQL.id == projeto_id))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(projeto_sql)
        return None

    async def get_by_nome(self, nome: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(ProjetoSQL).filter(ProjetoSQL.nome == nome))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(projeto_sql)
        return None

    async def get_by_codigo_empresa(self, codigo_empresa: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(ProjetoSQL).filter(ProjetoSQL.codigo_empresa == codigo_empresa))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(projeto_sql)
        return None

    async def get_by_jira_project_key(self, jira_project_key: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(ProjetoSQL).filter(ProjetoSQL.jira_project_key == jira_project_key))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(projeto_sql)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, status_projeto: Optional[int] = None) -> List[DomainProjeto]:
        async with self.db_session.begin():
            query = select(ProjetoSQL)
            if apenas_ativos:
                query = query.filter(ProjetoSQL.ativo == True)
            if status_projeto is not None:
                query = query.filter(ProjetoSQL.status_projeto == status_projeto)
            
            query = query.order_by(ProjetoSQL.nome).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            projetos_sql = result.scalars().all()
            return [DomainProjeto.model_validate(p) for p in projetos_sql]

    async def create(self, projeto_create_dto: ProjetoCreateDTO) -> DomainProjeto:
        new_projeto_sql = ProjetoSQL(**projeto_create_dto.model_dump())
        self.db_session.add(new_projeto_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_projeto_sql)
        return DomainProjeto.model_validate(new_projeto_sql)

    async def update(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[DomainProjeto]:
        projeto_sql = await self.db_session.get(ProjetoSQL, projeto_id)
        if not projeto_sql:
            return None

        update_data = projeto_update_dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(projeto_sql, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(projeto_sql)
        return DomainProjeto.model_validate(projeto_sql)

    async def delete(self, projeto_id: int) -> Optional[DomainProjeto]:
        projeto_to_delete_sql = await self.db_session.get(ProjetoSQL, projeto_id)
        if not projeto_to_delete_sql:
            return None
        
        projeto_domain = DomainProjeto.model_validate(projeto_to_delete_sql)
        await self.db_session.delete(projeto_to_delete_sql)
        await self.db_session.commit()
        return projeto_domain
