from typing import List, Optional
from app.db.orm_models import Projeto, AlocacaoRecursoProjeto, HorasPlanejadas
from app.application.dtos.projeto_dtos import ProjetoBaseDTO, ProjetoUpdateDTO, ProjetoDTO, ProjetoComAlocacoesCreateDTO
from app.application.dtos.projeto_detalhado_dtos import ProjetoDetalhadoDTO
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.status_projeto_repository import StatusProjetoRepository
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository as HorasPlanejadasRepository
from app.repositories.recurso_repository import RecursoRepository
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

class ProjetoService:
    def __init__(self,
                 projeto_repository: ProjetoRepository,
                 status_projeto_repository: StatusProjetoRepository,
                 alocacao_repository: AlocacaoRepository,
                 horas_planejadas_repository: HorasPlanejadasRepository,
                 recurso_repository: RecursoRepository):
        self.projeto_repository = projeto_repository
        self.status_projeto_repository = status_projeto_repository
        self.alocacao_repository = alocacao_repository
        self.horas_planejadas_repository = horas_planejadas_repository
        self.recurso_repository = recurso_repository

    async def get_projeto_by_id(self, projeto_id: int) -> Optional[ProjetoDTO]:
        projeto = await self.projeto_repository.get_by_id(projeto_id)
        if projeto:
            return ProjetoDTO.model_validate(projeto)
        return None

    async def get_all_projetos(self, skip: int = 0, limit: int = 100, include_inactive: bool = False, status_projeto: Optional[int] = None, search: Optional[str] = None) -> List[ProjetoDTO]:
        projetos = await self.projeto_repository.get_all(skip=skip, limit=limit, include_inactive=include_inactive, status_projeto=status_projeto, search=search)
        return [ProjetoDTO.model_validate(p) for p in projetos]

    async def count_projetos(self, include_inactive: bool = False, status_projeto: Optional[int] = None, search: Optional[str] = None) -> int:
        """Retorna a contagem total de projetos aplicando os mesmos filtros da listagem."""
        return await self.projeto_repository.count(include_inactive=include_inactive, status_projeto=status_projeto, search=search)

    async def create_projeto_com_alocacoes(self, data: ProjetoComAlocacoesCreateDTO, db_session: AsyncSession) -> ProjetoDTO:
        """
        Cria um projeto completo, incluindo suas alocações de recursos e as horas planejadas para cada alocação.
        Este método opera dentro de uma única transação para garantir a atomicidade.
        """
        async with db_session.begin():
            projeto_data_dto = data.projeto

            # Validações
            if not await self.status_projeto_repository.get_by_id(projeto_data_dto.status_projeto_id):
                raise HTTPException(status_code=400, detail=f"Status de projeto com ID {projeto_data_dto.status_projeto_id} não encontrado.")
            if await self.projeto_repository.get_by_nome(projeto_data_dto.nome):
                raise HTTPException(status_code=400, detail=f"Projeto com nome '{projeto_data_dto.nome}' já existe.")

            # 1. Criar Projeto (aceita tanto DTO quanto dict)
            if isinstance(projeto_data_dto, dict):
                projeto_dict = projeto_data_dto
            else:
                projeto_dict = projeto_data_dto.model_dump()
            created_projeto = await self.projeto_repository.create(projeto_dict)

            # 2. Iterar e Criar Alocações e Horas Planejadas
            if data.alocacoes:
                for aloc_dto in data.alocacoes:
                    # Converte Alocacao DTO para dict se necessário
                    aloc_dict_src = aloc_dto if isinstance(aloc_dto, dict) else aloc_dto.model_dump()
                    recurso_id = aloc_dict_src["recurso_id"]
                    if not await self.recurso_repository.get_by_id(recurso_id):
                        raise HTTPException(status_code=400, detail=f"Recurso com ID {aloc_dto.recurso_id} não encontrado.")

                    alocacao_dict = {
                        "recurso_id": recurso_id,
                        "projeto_id": created_projeto.id,
                        "data_inicio_alocacao": aloc_dict_src["data_inicio_alocacao"],
                        "data_fim_alocacao": aloc_dict_src["data_fim_alocacao"]
                    }
                    created_alocacao = await self.alocacao_repository.create(alocacao_dict)

                    horas_planejadas_list = aloc_dict_src.get("horas_planejadas", [])
                    for horas_item in horas_planejadas_list:
                        horas_dict_src = horas_item if isinstance(horas_item, dict) else horas_item.model_dump()
                        horas_dict = {
                            "alocacao_id": created_alocacao.id,
                            "ano": horas_dict_src["ano"],
                            "mes": horas_dict_src["mes"],
                            "horas_planejadas": horas_dict_src["horas_planejadas"]
                        }
                        await self.horas_planejadas_repository.create(horas_dict)
            
            # A chamada `refresh` foi removida pois o repositório já retorna um objeto de domínio atualizado.
            # A validação do Pydantic na saída garante a consistência do objeto retornado.
            return ProjetoDTO.model_validate(created_projeto)

    async def create_projeto(self, projeto_create_dto: ProjetoBaseDTO) -> ProjetoDTO:
        # Regra de negócio: secao_id agora é obrigatório
        if projeto_create_dto.secao_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campo 'secao_id' é obrigatório.")

        # Check if status_projeto_id exists
        status_projeto = await self.status_projeto_repository.get_by_id(projeto_create_dto.status_projeto_id)
        if not status_projeto:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Status de Projeto com ID {projeto_create_dto.status_projeto_id} não existe.")

        # Check for unique constraints: nome, codigo_empresa, jira_project_key
        if await self.projeto_repository.get_by_nome(projeto_create_dto.nome):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Projeto com nome \'{projeto_create_dto.nome}\' já existe.")
        if projeto_create_dto.codigo_empresa and await self.projeto_repository.get_by_codigo_empresa(projeto_create_dto.codigo_empresa):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Projeto com Código Empresa \'{projeto_create_dto.codigo_empresa}\' já existe.")
        if projeto_create_dto.jira_project_key and await self.projeto_repository.get_by_jira_project_key(projeto_create_dto.jira_project_key):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Projeto com Jira Project Key \'{projeto_create_dto.jira_project_key}\' já existe.")

        projeto = await self.projeto_repository.create(projeto_create_dto)
        return ProjetoDTO.model_validate(projeto)

    async def update_projeto(self, projeto_id: int, projeto_update_dto: ProjetoUpdateDTO) -> Optional[ProjetoDTO]:
        current_projeto = await self.projeto_repository.get_by_id(projeto_id)
        if not current_projeto:
            return None

        # Check if status_projeto_id is being updated and if the new status_projeto_id exists
        if projeto_update_dto.status_projeto_id is not None and projeto_update_dto.status_projeto_id != current_projeto.status_projeto_id:
            status_projeto = await self.status_projeto_repository.get_by_id(projeto_update_dto.status_projeto_id)
            if not status_projeto:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Novo Status de Projeto com ID {projeto_update_dto.status_projeto_id} não existe.")

        # Check for unique constraints if they are being changed
        if projeto_update_dto.nome and projeto_update_dto.nome != current_projeto.nome:
            if await self.projeto_repository.get_by_nome(projeto_update_dto.nome):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro projeto com nome \'{projeto_update_dto.nome}\' já existe.")
        
        if projeto_update_dto.codigo_empresa and projeto_update_dto.codigo_empresa != current_projeto.codigo_empresa:
            if await self.projeto_repository.get_by_codigo_empresa(projeto_update_dto.codigo_empresa):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro projeto com Código Empresa \'{projeto_update_dto.codigo_empresa}\' já existe.")

        if projeto_update_dto.jira_project_key and projeto_update_dto.jira_project_key != current_projeto.jira_project_key:
            if await self.projeto_repository.get_by_jira_project_key(projeto_update_dto.jira_project_key):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro projeto com Jira Project Key \'{projeto_update_dto.jira_project_key}\' já existe.")

        projeto = await self.projeto_repository.update(projeto_id, projeto_update_dto)
        if projeto:
            return ProjetoDTO.model_validate(projeto)
        return None

    async def get_projetos_detalhados(
        self,
        page: int = 1,
        per_page: int = 10,
        search: Optional[str] = None,
        ativo: Optional[bool] = None,
        com_alocacoes: bool = True,
        secao_id: Optional[int] = None,
        recurso: Optional[str] = None,
    ) -> List[ProjetoDetalhadoDTO]:
        skip = (page - 1) * per_page
        projetos = await self.projeto_repository.list_detalhados(
            skip=skip,
            limit=per_page,
            search=search,
            ativo=ativo,
            com_alocacoes=com_alocacoes,
            secao_id=secao_id,
            recurso=recurso,
        )
        return [ProjetoDetalhadoDTO.model_validate(p) for p in projetos]

    async def count_projetos_detalhados(
        self,
        search: Optional[str] = None,
        ativo: Optional[bool] = None,
        com_alocacoes: bool = True,
        secao_id: Optional[int] = None,
        recurso: Optional[str] = None,
    ) -> int:
        """Retorna a contagem total de projetos detalhados aplicando os mesmos filtros da listagem."""
        return await self.projeto_repository.count_detalhados(
            search=search,
            ativo=ativo,
            com_alocacoes=com_alocacoes,
            secao_id=secao_id,
            recurso=recurso,
        )

    async def delete_projeto(self, projeto_id: int) -> Optional[ProjetoDTO]:
        # Add logic here to check if projeto can be deleted (e.g., no active alocacoes or apontamentos)
        projeto_deletado = await self.projeto_repository.delete(projeto_id)
        if projeto_deletado:
            return ProjetoDTO.model_validate(projeto_deletado)
        return None
