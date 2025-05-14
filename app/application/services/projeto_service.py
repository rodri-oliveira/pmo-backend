from typing import List, Optional
from app.domain.models.projeto_model import Projeto
from app.application.dtos.projeto_dtos import ProjetoBaseDTO, ProjetoUpdateDTO, ProjetoDTO
from app.domain.repositories.projeto_repository import ProjetoRepository
from app.domain.repositories.status_projeto_repository import StatusProjetoRepository
from fastapi import HTTPException, status

class ProjetoService:
    def __init__(self, projeto_repository: ProjetoRepository, status_projeto_repository: StatusProjetoRepository):
        self.projeto_repository = projeto_repository
        self.status_projeto_repository = status_projeto_repository

    async def get_projeto_by_id(self, projeto_id: int) -> Optional[ProjetoDTO]:
        projeto = await self.projeto_repository.get_by_id(projeto_id)
        if projeto:
            return ProjetoDTO.model_validate(projeto)
        return None

    async def get_all_projetos(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, status_projeto: Optional[int] = None) -> List[ProjetoDTO]:
        projetos = await self.projeto_repository.get_all(skip=skip, limit=limit, apenas_ativos=apenas_ativos, status_projeto=status_projeto)
        return [ProjetoDTO.model_validate(p) for p in projetos]

    async def create_projeto(self, projeto_create_dto: ProjetoBaseDTO) -> ProjetoDTO:
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

    async def delete_projeto(self, projeto_id: int) -> Optional[ProjetoDTO]:
        # Add logic here to check if projeto can be deleted (e.g., no active alocacoes or apontamentos)
        projeto_deletado = await self.projeto_repository.delete(projeto_id)
        if projeto_deletado:
            return ProjetoDTO.model_validate(projeto_deletado)
        return None
