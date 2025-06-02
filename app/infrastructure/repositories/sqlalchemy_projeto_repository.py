from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_
from sqlalchemy.orm import selectinload
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

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, status_projeto: Optional[int] = None) -> List[DomainProjeto]:
        try:
            # Usar selectinload para carregar o relacionamento status_projeto
            query = select(Projeto).options(selectinload(Projeto.status_projeto))
            
            if apenas_ativos:
                query = query.filter(Projeto.ativo == True)
            if status_projeto is not None:
                query = query.filter(Projeto.status_projeto_id == status_projeto)
            
            query = query.order_by(Projeto.nome).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            projetos_sql = result.scalars().all()
            
            # Converter para lista de objetos de domínio
            return [DomainProjeto.model_validate(self._to_dict(p)) for p in projetos_sql]
        except Exception as e:
            # Log do erro para diagnóstico
            error_msg = str(e)
            print(f"Erro ao listar projetos: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {error_msg}")

    async def create(self, projeto_create_dto: ProjetoCreateDTO) -> DomainProjeto:
        try:
            # Extrair dados do DTO
            data = projeto_create_dto.model_dump()
            
            # Adicionar manualmente as datas
            now = datetime.now()
            data["data_criacao"] = now
            data["data_atualizacao"] = now
            
            # Criar o objeto SQL e salvá-lo
            new_projeto_sql = Projeto(**data)
            self.db_session.add(new_projeto_sql)
            await self.db_session.commit()
            await self.db_session.refresh(new_projeto_sql)
            
            # Converter para dicionário antes de validar
            projeto_dict = self._to_dict(new_projeto_sql)
            return DomainProjeto.model_validate(projeto_dict)
        except Exception as e:
            # Rollback em caso de erro
            await self.db_session.rollback()
            
            # Identificar tipos específicos de erros
            error_msg = str(e)
            if "violates unique constraint" in error_msg:
                if "projeto_nome_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe um projeto com este nome.")
                elif "projeto_codigo_empresa_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe um projeto com este código de empresa.")
                elif "projeto_jira_project_key_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe um projeto com esta chave de projeto Jira.")
                else:
                    raise HTTPException(status_code=400, detail=f"Violação de restrição única: {error_msg}")
            elif "violates foreign key constraint" in error_msg and "status_projeto_id" in error_msg:
                raise HTTPException(status_code=400, detail=f"O status de projeto informado não existe.")
            else:
                # Log do erro para diagnóstico
                print(f"Erro ao criar projeto: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Erro ao criar projeto: {error_msg}")

    async def update(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[DomainProjeto]:
        try:
            projeto_sql = await self.db_session.get(Projeto, projeto_id)
            if not projeto_sql:
                return None

            update_data = projeto_update_dto.model_dump(exclude_unset=True)
            update_data["data_atualizacao"] = datetime.now()
            
            for key, value in update_data.items():
                setattr(projeto_sql, key, value)
                
            await self.db_session.commit()
            await self.db_session.refresh(projeto_sql)
            
            projeto_dict = self._to_dict(projeto_sql)
            return DomainProjeto.model_validate(projeto_dict)
        except Exception as e:
            # Rollback em caso de erro
            await self.db_session.rollback()
            
            # Identificar tipos específicos de erros
            error_msg = str(e)
            if "violates unique constraint" in error_msg:
                if "projeto_nome_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe outro projeto com este nome.")
                elif "projeto_codigo_empresa_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe outro projeto com este código de empresa.")
                elif "projeto_jira_project_key_key" in error_msg:
                    raise HTTPException(status_code=400, detail=f"Já existe outro projeto com esta chave de projeto Jira.")
                else:
                    raise HTTPException(status_code=400, detail=f"Violação de restrição única: {error_msg}")
            elif "violates foreign key constraint" in error_msg and "status_projeto_id" in error_msg:
                raise HTTPException(status_code=400, detail=f"O status de projeto informado não existe.")
            else:
                # Log do erro para diagnóstico
                print(f"Erro ao atualizar projeto: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {error_msg}")

    async def delete(self, projeto_id: int) -> Optional[DomainProjeto]:
        try:
            projeto_to_delete_sql = await self.db_session.get(Projeto, projeto_id)
            if not projeto_to_delete_sql:
                return None
            
            # Exclusão lógica - apenas marca como inativo
            projeto_to_delete_sql.ativo = False
            projeto_to_delete_sql.data_atualizacao = datetime.now(timezone.utc)
            
            await self.db_session.commit()
            await self.db_session.refresh(projeto_to_delete_sql)
            
            projeto_dict = self._to_dict(projeto_to_delete_sql)
            return DomainProjeto.model_validate(projeto_dict)
        except Exception as e:
            # Rollback em caso de erro
            await self.db_session.rollback()
            
            # Identificar tipos específicos de erros
            error_msg = str(e)
            if "violates unique constraint" in error_msg:
                raise HTTPException(status_code=400, detail=f"Violação de restrição única: {error_msg}")
            elif "violates foreign key constraint" in error_msg:
                raise HTTPException(status_code=400, detail=f"Violação de restrição de chave estrangeira: {error_msg}")
            else:
                # Log do erro para diagnóstico
                print(f"Erro ao excluir projeto: {error_msg}")
                raise HTTPException(status_code=500, detail=f"Erro ao excluir projeto: {error_msg}")
