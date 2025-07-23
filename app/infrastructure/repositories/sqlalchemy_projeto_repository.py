import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_, or_, func
from sqlalchemy.orm import selectinload, with_loader_criteria
from sqlalchemy.dialects import postgresql
from datetime import datetime, timezone
from sqlalchemy.orm import class_mapper
from app.domain.models.projeto_model import Projeto as DomainProjeto
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO
from app.domain.repositories.projeto_repository import ProjetoRepository
from app.db.orm_models import Equipe, Projeto, AlocacaoRecursoProjeto, Recurso
from sqlalchemy.exc import SQLAlchemyError
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

    async def create(self, projeto_data) -> DomainProjeto:
        try:
            # Verifica se já é um dicionário ou se precisa converter
            if isinstance(projeto_data, dict):
                projeto_dict = projeto_data
            else:
                projeto_dict = projeto_data.model_dump()  # Usa model_dump() ao invés de dict()
            novo_projeto_sql = Projeto(**projeto_dict)
            self.db_session.add(novo_projeto_sql)
            # Flush para gerar o ID
            await self.db_session.flush()
            await self.db_session.refresh(novo_projeto_sql)
            # Não fazer commit aqui - deixar para o serviço controlar a transação
            return DomainProjeto.model_validate(self._to_dict(novo_projeto_sql))
        except SQLAlchemyError as e:
            # O rollback é gerenciado pelo service layer com o `async with db_session.begin()`
            logging.error(f"Erro ao criar projeto no repositório: {e}")
            raise

    async def count(self, apenas_ativos: bool = True, status_projeto: Optional[int] = None, search: Optional[str] = None, **kwargs) -> int:
        """Conta o total de projetos após aplicar os mesmos filtros da listagem."""
        # Compatibilidade com include_inactive
        if "include_inactive" in kwargs and kwargs["include_inactive"] is not None:
            apenas_ativos = not kwargs["include_inactive"]

        query = select(func.count()).select_from(Projeto)

        if search:
            query = query.where(or_(
                Projeto.nome.ilike(func.concat('%', search, '%')),
                Projeto.codigo_empresa.ilike(func.concat('%', search, '%')),
                Projeto.descricao.ilike(func.concat('%', search, '%'))
            ))
        if apenas_ativos:
            query = query.where(Projeto.ativo.is_(True))
        if status_projeto is not None:
            query = query.where(Projeto.status_projeto_id == status_projeto)

        result = await self.db_session.execute(query)
        return result.scalar_one()

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = True, status_projeto: Optional[int] = None, search: Optional[str] = None, **kwargs) -> List[DomainProjeto]:
        # Compatibilidade: se a camada superior ainda enviar 'include_inactive', convertemos.
        if "include_inactive" in kwargs and kwargs["include_inactive"] is not None:
            # include_inactive=True significa queremos TODOS (apenas_ativos=False)
            apenas_ativos = not kwargs["include_inactive"]
        logger = logging.getLogger("app.repositories.sqlalchemy_projeto_repository")
        try:
            query = select(Projeto).options(selectinload(Projeto.status))

            logger.info(f"Repository get_all received: search='{search}', apenas_ativos={apenas_ativos}")

            if search:
                query = query.filter(or_(
                    Projeto.nome.ilike(func.concat('%', search, '%')),
                    Projeto.codigo_empresa.ilike(func.concat('%', search, '%')),
                    Projeto.descricao.ilike(func.concat('%', search, '%'))
                ))
                logger.info(f"Applying search filter for term: '{search}'")

            # Por padrão (apenas_ativos=True), busca apenas projetos ativos.
            # Se apenas_ativos=False, a cláusula não é adicionada, retornando todos.
            if apenas_ativos:
                query = query.filter(Projeto.ativo.is_(True))

            if status_projeto is not None:
                query = query.filter(Projeto.status_projeto_id == status_projeto)
            
            query = query.order_by(Projeto.nome).offset(skip).limit(limit)
            
            try:
                compiled_query = query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
                logger.info(f"Executing query: {compiled_query}")
            except Exception as compilation_error:
                logger.error(f"Error compiling query: {compilation_error}")

            # Executa a consulta
            result = await self.db_session.execute(query)
            projetos_sql = result.scalars().all()

            return [DomainProjeto.model_validate(self._to_dict(p)) for p in projetos_sql]
        except Exception as e:
            logger.error(f"Erro ao listar projetos: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao listar projetos: {str(e)}")
            return None
        except Exception as e:
            await self.db_session.rollback()
            error_msg = str(e)
            # Adicionar tratamento de erro mais específico se necessário
            logger.error(f"Erro ao atualizar projeto: {error_msg}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {error_msg}")

    async def update(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[DomainProjeto]:
        """Atualiza um projeto existente."""
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
            updated_sql = result.scalar_one_or_none()
            if updated_sql:
                return DomainProjeto.model_validate(self._to_dict(updated_sql))
            return None
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Erro ao atualizar projeto: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar projeto: {str(e)}")

    async def list_detalhados(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        ativo: Optional[bool] = None,
        com_alocacoes: Optional[bool] = None,
        secao_id: Optional[int] = None,
        recurso: Optional[str] = None,
    ) -> List[Projeto]:
        """Lista projetos com dados aninhados (alocações, horas planejadas) em única consulta."""
        logger = logging.getLogger("app.repositories.sqlalchemy_projeto_repository")
        try:
            query = select(Projeto).options(
                selectinload(Projeto.secao),
                selectinload(Projeto.status),
                selectinload(Projeto.alocacoes).selectinload(AlocacaoRecursoProjeto.recurso),
                selectinload(Projeto.alocacoes).selectinload(AlocacaoRecursoProjeto.status_alocacao),
                selectinload(Projeto.alocacoes).selectinload(AlocacaoRecursoProjeto.horas_planejadas),
                selectinload(Projeto.alocacoes).selectinload(AlocacaoRecursoProjeto.equipe) # Carrega a equipe associada
            )

            if search:
                query = query.where(
                    or_(
                        Projeto.nome.ilike(func.concat('%', search, '%')),
                        Projeto.descricao.ilike(func.concat('%', search, '%')),
                    )
                )
            
            if ativo is not None:
                query = query.where(Projeto.ativo.is_(ativo))

            if com_alocacoes:
                query = query.where(Projeto.alocacoes.any())

            if secao_id is not None:
                query = query.where(Projeto.secao_id == secao_id)

            if recurso:
                recurso_term = recurso.strip()
                if recurso_term and recurso_term.isdigit():
                    recurso_id = int(recurso_term)
                    recurso_filter = (AlocacaoRecursoProjeto.recurso_id == recurso_id)
                    query = query.where(Projeto.alocacoes.any(recurso_filter))
                    query = query.options(with_loader_criteria(AlocacaoRecursoProjeto, recurso_filter))
                elif recurso_term:
                    recurso_filter = AlocacaoRecursoProjeto.recurso.has(Recurso.nome.ilike(recurso_term + "%"))
                    query = query.where(Projeto.alocacoes.any(recurso_filter))
                    query = query.options(with_loader_criteria(AlocacaoRecursoProjeto, recurso_filter))

            query = query.order_by(Projeto.id.asc()).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            projetos_sql = result.scalars().unique().all()
            return projetos_sql
        except Exception as e:
            logger.error("Erro ao listar projetos detalhados: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao listar projetos detalhados")

    async def count_detalhados(
        self,
        search: Optional[str] = None,
        ativo: Optional[bool] = None,
        com_alocacoes: Optional[bool] = None,
        secao_id: Optional[int] = None,
        recurso: Optional[str] = None,
    ) -> int:
        """Conta o total de projetos detalhados aplicando os mesmos filtros."""
        try:
            query = select(func.count()).select_from(Projeto)

            if search:
                query = query.where(
                    or_(
                        Projeto.nome.ilike(func.concat('%', search, '%')),
                        Projeto.descricao.ilike(func.concat('%', search, '%')),
                    )
                )
            if ativo is not None:
                query = query.where(Projeto.ativo.is_(ativo))
            if com_alocacoes:
                query = query.where(Projeto.alocacoes.any())
            if secao_id is not None:
                query = query.where(Projeto.secao_id == secao_id)
            if recurso:
                recurso_term = recurso.strip()
                if recurso_term.isdigit():
                    # Filtro por ID
                    query = query.where(
                        Projeto.alocacoes.any(
                            AlocacaoRecursoProjeto.recurso_id == int(recurso_term)
                        )
                    )
                else:
                    # Filtro por início do nome (case-insensitive)
                    query = query.where(
                        Projeto.alocacoes.any(
                            AlocacaoRecursoProjeto.recurso.has(
                                Recurso.nome.ilike(recurso_term + '%')
                            )
                        )
                    )

            result = await self.db_session.execute(query)
            return result.scalar_one()
        except Exception as e:
            logging.getLogger("app.repositories.sqlalchemy_projeto_repository").error("Erro ao contar projetos detalhados: %s", str(e), exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao contar projetos detalhados")

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
