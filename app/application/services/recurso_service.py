from typing import List, Optional
from app.domain.models.recurso_model import Recurso
from app.application.dtos.recurso_dtos import RecursoCreateDTO, RecursoUpdateDTO, RecursoDTO
from app.domain.repositories.recurso_repository import RecursoRepository
from app.domain.repositories.equipe_repository import EquipeRepository # To check if equipe_id exists
from fastapi import HTTPException, status

class RecursoService:
    def __init__(self, recurso_repository: RecursoRepository, equipe_repository: EquipeRepository):
        self.recurso_repository = recurso_repository
        self.equipe_repository = equipe_repository

    async def get_recurso_by_id(self, recurso_id: int) -> Optional[RecursoDTO]:
        recurso = await self.recurso_repository.get_by_id(recurso_id)
        if recurso:
            return RecursoDTO.model_validate(recurso)
        return None

    async def get_all_recursos(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, equipe_id: Optional[int] = None) -> List[RecursoDTO]:
        recursos = await self.recurso_repository.get_all(skip=skip, limit=limit, apenas_ativos=apenas_ativos, equipe_id=equipe_id)
        return [RecursoDTO.model_validate(recurso) for recurso in recursos]

    async def create_recurso(self, recurso_create_dto: RecursoCreateDTO) -> RecursoDTO:
        # Check if email already exists
        recurso_existente_email = await self.recurso_repository.get_by_email(recurso_create_dto.email)
        if recurso_existente_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Recurso com email \'{recurso_create_dto.email}\' já existe.")

        # Check if matricula already exists (if provided)
        if recurso_create_dto.matricula:
            recurso_existente_matricula = await self.recurso_repository.get_by_matricula(recurso_create_dto.matricula)
            if recurso_existente_matricula:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Recurso com matrícula \'{recurso_create_dto.matricula}\' já existe.")

        # Check if jira_user_id already exists (if provided)
        if recurso_create_dto.jira_user_id:
            recurso_existente_jira = await self.recurso_repository.get_by_jira_user_id(recurso_create_dto.jira_user_id)
            if recurso_existente_jira:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Recurso com Jira User ID \'{recurso_create_dto.jira_user_id}\' já existe.")

        # Check if equipe_principal_id exists and is active (if provided)
        if recurso_create_dto.equipe_principal_id is not None:
            equipe = await self.equipe_repository.get_by_id(recurso_create_dto.equipe_principal_id)
            if not equipe:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Equipe principal com ID {recurso_create_dto.equipe_principal_id} não existe.")
            if not equipe.ativo:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Equipe principal com ID {recurso_create_dto.equipe_principal_id} não está ativa.")

        recurso = await self.recurso_repository.create(recurso_create_dto)
        return RecursoDTO.model_validate(recurso)

    async def update_recurso(self, recurso_id: int, recurso_update_dto: RecursoUpdateDTO) -> Optional[RecursoDTO]:
        # Fetch current recurso to compare unique fields if they are being changed
        current_recurso = await self.recurso_repository.get_by_id(recurso_id)
        if not current_recurso:
            return None # Recurso not found

        # Check for email conflict
        if recurso_update_dto.email and recurso_update_dto.email != current_recurso.email:
            recurso_existente_email = await self.recurso_repository.get_by_email(recurso_update_dto.email)
            if recurso_existente_email and recurso_existente_email.id != recurso_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro recurso com email \'{recurso_update_dto.email}\' já existe.")

        # Check for matricula conflict
        if recurso_update_dto.matricula and recurso_update_dto.matricula != current_recurso.matricula:
            recurso_existente_matricula = await self.recurso_repository.get_by_matricula(recurso_update_dto.matricula)
            if recurso_existente_matricula and recurso_existente_matricula.id != recurso_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro recurso com matrícula \'{recurso_update_dto.matricula}\' já existe.")

        # Check for jira_user_id conflict
        if recurso_update_dto.jira_user_id and recurso_update_dto.jira_user_id != current_recurso.jira_user_id:
            recurso_existente_jira = await self.recurso_repository.get_by_jira_user_id(recurso_update_dto.jira_user_id)
            if recurso_existente_jira and recurso_existente_jira.id != recurso_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Outro recurso com Jira User ID \'{recurso_update_dto.jira_user_id}\' já existe.")

        # Check if equipe_principal_id exists and is active (if provided and changed)
        if recurso_update_dto.equipe_principal_id is not None and recurso_update_dto.equipe_principal_id != current_recurso.equipe_principal_id:
            equipe = await self.equipe_repository.get_by_id(recurso_update_dto.equipe_principal_id)
            if not equipe:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nova equipe principal com ID {recurso_update_dto.equipe_principal_id} não existe.")
            if not equipe.ativo:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Nova equipe principal com ID {recurso_update_dto.equipe_principal_id} não está ativa.")

        recurso = await self.recurso_repository.update(recurso_id, recurso_update_dto)
        if recurso:
            return RecursoDTO.model_validate(recurso)
        return None

    async def delete_recurso(self, recurso_id: int) -> Optional[RecursoDTO]:
        # Add logic here to check if recurso can be deleted (e.g., no active alocacoes)
        recurso_deletado = await self.recurso_repository.delete(recurso_id)
        if recurso_deletado:
            return RecursoDTO.model_validate(recurso_deletado)
        return None
