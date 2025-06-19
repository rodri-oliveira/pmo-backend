import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone
from sqlalchemy.orm import class_mapper
from app.domain.models.projeto_model import Projeto as DomainProjeto
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO
from app.domain.repositories.projeto_repository import ProjetoRepository
from app.db.orm_models import Projeto
from fastapi import HTTPException

class SQLAlchemyProjetoRepository(ProjetoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    def _to_dict(self, obj):
        """Converte um objeto SQLAlchemy para dicionário"""
        if obj is None:
            return None
        return {c.key: getattr(obj, c.key) for c in class_mapper(obj.__class__).columns}

    async def get_by_id(self, projeto_id: int) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(Projeto).filter(Projeto.id == projeto_id))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(self._to_dict(projeto_sql))
        return None

    async def get_by_nome(self, nome: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(Projeto).filter(Projeto.nome == nome))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(self._to_dict(projeto_sql))
        return None

    async def get_by_codigo_empresa(self, codigo_empresa: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(Projeto).filter(Projeto.codigo_empresa == codigo_empresa))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(self._to_dict(projeto_sql))
        return None

    async def get_by_jira_project_key(self, jira_project_key: str) -> Optional[DomainProjeto]:
        result = await self.db_session.execute(select(Projeto).filter(Projeto.jira_project_key == jira_project_key))
        projeto_sql = result.scalars().first()
        if projeto_sql:
            return DomainProjeto.model_validate(self._to_dict(projeto_sql))
        return None

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, status_projeto: Optional[int] = None, search: Optional[str] = None) -> List[DomainProjeto]:
        logger = logging.getLogger("app.repositories.sqlalchemy_projeto_repository")
        try:
            query = select(Projeto).options(selectinload(Projeto.status))

            logger.info(f"Repository get_all received: search='{search}', apenas_ativos={apenas_ativos}")

            if search:
                query = query.filter(Projeto.nome.ilike(func.concat('%', search, '%')))
                logger.info(f"Applying search filter for term: '{search}'")

            if apenas_ativos:
                query = query.filter(Projeto.ativo == True)

            if status_projeto is not None:
                query = query.filter(Projeto.status_projeto_id == status_projeto)
            
            query = query.order_by(Projeto.nome).offset(skip).limit(limit)
            
            try:
                compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
                logger.info(f"Executing query: {compiled_query}")
            except Exception as compilation_error:
                logger.error(f"Error compiling query: {compilation_error}")

            result = await self.db_session.execute(query)
            projetos_sql = result.scalars().all()
            
            return [DomainProjeto.model_validate(self._to_dict(p)) for p in projetos_sql]
        except Exception as e:
            logger.error(f"Erro ao listar projetos: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {str(e)}")

    async def create(self, projeto_create_dto: ProjetoCreateDTO) -> DomainProjeto:
        try:
            data = projeto_create_dto.model_dump()
            
            # Criar dicionário apenas com campos obrigatórios
            projeto_data = {
                "nome": data["nome"],
                "status_projeto_id": data["status_projeto_id"],
                "ativo": data.get("ativo", True)
            }
            
            # Adicionar campos opcionais apenas se presentes e não nulos
            campos_opcionais = [
                "jira_project_key", "secao_id", "descricao", "codigo_empresa",
                "data_inicio_prevista", "data_fim_prevista"
            ]
            
            for campo in campos_opcionais:
                if campo in data and data[campo] is not None:
                    projeto_data[campo] = data[campo]
            
            # Tratar datas especiais - usar apenas se fornecidas explicitamente
            if "data_criacao" in data and data["data_criacao"] is not None:
                projeto_data["data_criacao"] = data["data_criacao"]
            
            if "data_atualizacao" in data and data["data_atualizacao"] is not None:
                projeto_data["data_atualizacao"] = data["data_atualizacao"]
            
            # Criar objeto apenas com dados válidos
            new_projeto_sql = Projeto(**projeto_data)
            
            self.db_session.add(new_projeto_sql)
            await self.db_session.flush()
            await self.db_session.commit()
            await self.db_session.refresh(new_projeto_sql)
            
            return DomainProjeto.model_validate(self._to_dict(new_projeto_sql))
        except Exception as e:
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar projeto: {str(e)}"
            )

    async def update(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[DomainProjeto]:
        try:
            update_data = projeto_update_dto.model_dump(exclude_unset=True)
            if not update_data:
                return await self.get_by_id(projeto_id)

            query = (
                sqlalchemy_update(Projeto)
                .where(Projeto.id == projeto_id)
                .values(**update_data)
                .returning(Projeto)
            )
            
            result = await self.db_session.execute(query)
            await self.db_session.commit()
            updated_projeto_sql = result.scalar_one_or_none()

            if updated_projeto_sql:
                return DomainProjeto.model_validate(self._to_dict(updated_projeto_sql))
            
            return None
        except Exception as e:
            await self.db_session.rollback()
            error_msg = str(e)
            # Adicionar tratamento de erro mais específico se necessário
            logger.error(f"Erro ao atualizar projeto: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {error_msg}")

    async def delete(self, projeto_id: int) -> Optional[DomainProjeto]:
        try:
            query = (
                sqlalchemy_update(Projeto)
                .where(Projeto.id == projeto_id)
                .values(ativo=False)  # data_atualizacao é gerenciada pelo DB
                .returning(Projeto)
            )
            result = await self.db_session.execute(query)
            await self.db_session.commit()
            
            deleted_projeto_sql = result.scalar_one_or_none()

            if deleted_projeto_sql:
                return DomainProjeto.model_validate(self._to_dict(deleted_projeto_sql))

            return None
        except Exception as e:
            await self.db_session.rollback()
            error_msg = str(e)
            logger.error(f"Erro ao excluir projeto: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao excluir projeto: {error_msg}")
