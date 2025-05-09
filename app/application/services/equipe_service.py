from typing import List, Optional
from app.domain.models.equipe_model import Equipe
from app.application.dtos.equipe_dtos import EquipeCreateDTO, EquipeUpdateDTO, EquipeDTO
from app.domain.repositories.equipe_repository import EquipeRepository
from app.domain.repositories.secao_repository import SecaoRepository # To check if secao_id exists
from fastapi import HTTPException, status

class EquipeService:
    def __init__(self, equipe_repository: EquipeRepository, secao_repository: SecaoRepository):
        self.equipe_repository = equipe_repository
        self.secao_repository = secao_repository

    async def get_equipe_by_id(self, equipe_id: int) -> Optional[EquipeDTO]:
        equipe = await self.equipe_repository.get_by_id(equipe_id)
        if equipe:
            return EquipeDTO.from_orm(equipe)
        return None

    async def get_all_equipes(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[EquipeDTO]:
        equipes = await self.equipe_repository.get_all(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
        return [EquipeDTO.from_orm(equipe) for equipe in equipes]

    async def get_equipes_by_secao_id(self, secao_id: int, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[EquipeDTO]:
        secao = await self.secao_repository.get_by_id(secao_id)
        if not secao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Seção com ID {secao_id} não encontrada.")
        equipes = await self.equipe_repository.get_all_by_secao_id(secao_id=secao_id, skip=skip, limit=limit, apenas_ativos=apenas_ativos)
        return [EquipeDTO.from_orm(equipe) for equipe in equipes]

    async def create_equipe(self, equipe_create_dto: EquipeCreateDTO) -> EquipeDTO:
        # Check if secao_id exists
        secao = await self.secao_repository.get_by_id(equipe_create_dto.secao_id)
        if not secao:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Seção com ID {equipe_create_dto.secao_id} não existe.")
        if not secao.ativo:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Seção com ID {equipe_create_dto.secao_id} não está ativa.")

        # Check if equipe with the same name already exists in the same secao
        equipe_existente = await self.equipe_repository.get_by_nome_and_secao_id(equipe_create_dto.nome, equipe_create_dto.secao_id)
        if equipe_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma equipe com o nome \'{equipe_create_dto.nome}\' na seção ID {equipe_create_dto.secao_id}."
            )
        
        equipe = await self.equipe_repository.create(equipe_create_dto)
        return EquipeDTO.from_orm(equipe)

    async def update_equipe(self, equipe_id: int, equipe_update_dto: EquipeUpdateDTO) -> Optional[EquipeDTO]:
        # Check if secao_id is being updated and if the new secao_id exists
        if equipe_update_dto.secao_id is not None:
            secao = await self.secao_repository.get_by_id(equipe_update_dto.secao_id)
            if not secao:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nova Seção com ID {equipe_update_dto.secao_id} não existe.")
            if not secao.ativo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nova Seção com ID {equipe_update_dto.secao_id} não está ativa.")

        # Check for name conflict if name is being updated
        if equipe_update_dto.nome is not None:
            # Need to know the current secao_id if it's not being changed, or the new one if it is
            current_equipe = await self.equipe_repository.get_by_id(equipe_id)
            if not current_equipe:
                 return None # Equipe not found, update will also fail in repo but good to check early
            
            target_secao_id = equipe_update_dto.secao_id if equipe_update_dto.secao_id is not None else current_equipe.secao_id
            equipe_existente = await self.equipe_repository.get_by_nome_and_secao_id(equipe_update_dto.nome, target_secao_id)
            if equipe_existente and equipe_existente.id != equipe_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Já existe outra equipe com o nome \'{equipe_update_dto.nome}\' na seção ID {target_secao_id}."
                )

        equipe = await self.equipe_repository.update(equipe_id, equipe_update_dto)
        if equipe:
            return EquipeDTO.from_orm(equipe)
        return None

    async def delete_equipe(self, equipe_id: int) -> Optional[EquipeDTO]:
        # Add logic here to check if equipe can be deleted (e.g., no active resources)
        equipe_deletada = await self.equipe_repository.delete(equipe_id)
        if equipe_deletada:
            return EquipeDTO.from_orm(equipe_deletada)
        return None

