from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_

from app.domain.models.secao_model import Secao as DomainSecao
from app.application.dtos.secao_dtos import SecaoCreateDTO, SecaoUpdateDTO
from app.domain.repositories.secao_repository import SecaoRepository
from app.infrastructure.database.secao_sql_model import SecaoSQL

class SQLAlchemySecaoRepository(SecaoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, secao_id: int) -> Optional[DomainSecao]:
        result = await self.db_session.execute(select(SecaoSQL).filter(SecaoSQL.id == secao_id))
        secao_sql = result.scalars().first()
        if secao_sql:
            return DomainSecao.model_validate(secao_sql) # Pydantic V2
        return None

    async def get_by_nome(self, nome: str) -> Optional[DomainSecao]:
        result = await self.db_session.execute(select(SecaoSQL).filter(SecaoSQL.nome == nome))
        secao_sql = result.scalars().first()
        if secao_sql:
            return DomainSecao.model_validate(secao_sql)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[DomainSecao]:
        query = select(SecaoSQL)
        if apenas_ativos:
            query = query.filter(SecaoSQL.ativo == True)
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        secoes_sql = result.scalars().all()
        return [DomainSecao.model_validate(secao) for secao in secoes_sql]

    async def create(self, secao_create_dto: SecaoCreateDTO) -> DomainSecao:
        new_secao_sql = SecaoSQL(
            nome=secao_create_dto.nome,
            descricao=secao_create_dto.descricao
        )
        self.db_session.add(new_secao_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_secao_sql)
        return DomainSecao.model_validate(new_secao_sql)

    async def update(self, secao_id: int, secao_update_dto: SecaoUpdateDTO) -> Optional[DomainSecao]:
        # Fetch the existing record first to ensure it exists
        secao_sql = await self.db_session.get(SecaoSQL, secao_id)
        if not secao_sql:
            return None

        update_data = secao_update_dto.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(secao_sql, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(secao_sql)
        return DomainSecao.model_validate(secao_sql)

    async def delete(self, secao_id: int) -> Optional[DomainSecao]:
        secao_to_delete_sql = await self.db_session.get(SecaoSQL, secao_id)
        if not secao_to_delete_sql:
            return None
        
        # For soft delete, we update the 'ativo' flag
        # secao_to_delete_sql.ativo = False
        # await self.db_session.commit()
        # await self.db_session.refresh(secao_to_delete_sql)
        # return DomainSecao.model_validate(secao_to_delete_sql)

        # For hard delete:
        secao_domain = DomainSecao.model_validate(secao_to_delete_sql) # convert before deleting
        await self.db_session.delete(secao_to_delete_sql)
        await self.db_session.commit()
        return secao_domain

