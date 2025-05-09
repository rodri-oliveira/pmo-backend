from typing import List, Optional
from app.domain.models.status_projeto_model import StatusProjeto
from app.application.dtos.status_projeto_dtos import StatusProjetoCreateDTO, StatusProjetoUpdateDTO, StatusProjetoDTO
from app.domain.repositories.status_projeto_repository import StatusProjetoRepository
from fastapi import HTTPException, status

class StatusProjetoService:
    def __init__(self, status_projeto_repository: StatusProjetoRepository):
        self.status_projeto_repository = status_projeto_repository

    async def get_status_projeto_by_id(self, status_id: int) -> Optional[StatusProjetoDTO]:
        status_projeto = await self.status_projeto_repository.get_by_id(status_id)
        if status_projeto:
            return StatusProjetoDTO.from_orm(status_projeto)
        return None

    async def get_all_status_projeto(self, skip: int = 0, limit: int = 100) -> List[StatusProjetoDTO]:
        status_projetos = await self.status_projeto_repository.get_all(skip=skip, limit=limit)
        return [StatusProjetoDTO.from_orm(sp) for sp in status_projetos]

    async def create_status_projeto(self, status_create_dto: StatusProjetoCreateDTO) -> StatusProjetoDTO:
        # Check if status with the same name already exists
        status_existente = await self.status_projeto_repository.get_by_nome(status_create_dto.nome)
        if status_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um status de projeto com o nome \'{status_create_dto.nome}\"."
            )
        # Check if ordem_exibicao is unique if provided
        # This logic might be better in the repository or DB constraint if possible
        if status_create_dto.ordem_exibicao is not None:
            # Query for existing status with the same ordem_exibicao
            # For simplicity, this check is omitted here but should be considered
            pass 

        status_projeto = await self.status_projeto_repository.create(status_create_dto)
        return StatusProjetoDTO.from_orm(status_projeto)

    async def update_status_projeto(self, status_id: int, status_update_dto: StatusProjetoUpdateDTO) -> Optional[StatusProjetoDTO]:
        # Check for name conflict if name is being updated
        if status_update_dto.nome:
            status_existente = await self.status_projeto_repository.get_by_nome(status_update_dto.nome)
            if status_existente and status_existente.id != status_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Já existe outro status de projeto com o nome \'{status_update_dto.nome}\"."
                )
        
        # Add similar check for ordem_exibicao if it needs to be unique and is being updated

        status_projeto = await self.status_projeto_repository.update(status_id, status_update_dto)
        if status_projeto:
            return StatusProjetoDTO.from_orm(status_projeto)
        return None

    async def delete_status_projeto(self, status_id: int) -> Optional[StatusProjetoDTO]:
        # Add logic here to check if status_projeto can be deleted (e.g., not in use by any projeto)
        status_deletado = await self.status_projeto_repository.delete(status_id)
        if status_deletado:
            return StatusProjetoDTO.from_orm(status_deletado)
        return None

