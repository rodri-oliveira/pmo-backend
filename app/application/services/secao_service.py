from typing import List, Optional
from app.domain.models.secao_model import Secao
from app.application.dtos.secao_dtos import SecaoCreateDTO, SecaoUpdateDTO, SecaoDTO
from app.domain.repositories.secao_repository import SecaoRepository
from app.domain.repositories.equipe_repository import EquipeRepository # Import EquipeRepository
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

class SecaoService:
    def __init__(self, secao_repository: SecaoRepository, equipe_repository: EquipeRepository): # Add equipe_repository
        self.secao_repository = secao_repository
        self.equipe_repository = equipe_repository # Store equipe_repository

    async def get_secao_by_id(self, secao_id: int) -> Optional[SecaoDTO]:
        secao = await self.secao_repository.get_by_id(secao_id)
        if secao:
            return SecaoDTO.model_validate(secao) # Pydantic V1
            # For Pydantic V2, use SecaoDTO.model_validate(secao)
        return None

    async def get_secao_by_nome(self, nome: str) -> Optional[SecaoDTO]:
        secao = await self.secao_repository.get_by_nome(nome)
        if secao:
            return SecaoDTO.model_validate(secao)
        return None

    async def get_all_secoes(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[SecaoDTO]:
        secoes = await self.secao_repository.get_all(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
        return [SecaoDTO.model_validate(secao) for secao in secoes]

    async def create_secao(self, secao_create_dto: SecaoCreateDTO) -> SecaoDTO:
        secao_existente = await self.secao_repository.get_by_nome(secao_create_dto.nome)
        if secao_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe uma seção com o nome \'{secao_create_dto.nome}\'."
            )
        secao = await self.secao_repository.create(secao_create_dto)
        return SecaoDTO.model_validate(secao)

    async def update_secao(self, secao_id: int, secao_update_dto: SecaoUpdateDTO) -> Optional[SecaoDTO]:
        if secao_update_dto.nome:
            secao_existente = await self.secao_repository.get_by_nome(secao_update_dto.nome)
            if secao_existente and secao_existente.id != secao_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Já existe outra seção com o nome \'{secao_update_dto.nome}\'."
                )
        
        secao = await self.secao_repository.update(secao_id, secao_update_dto)
        if secao:
            return SecaoDTO.model_validate(secao)
        return None

    

    async def delete_secao(self, secao_id: int) -> Optional[SecaoDTO]:
        try:
            # Checagem de equipes ativas (já existe no seu serviço)
            equipes_na_secao = await self.equipe_repository.get_all_by_secao_id(secao_id=secao_id, apenas_ativos=True)
            if equipes_na_secao:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Não é possível excluir a seção ID {secao_id} pois ela possui equipes ativas vinculadas."
                )
            # Chamada ao repositório (pode levantar exceção de dependentes)
            secao_deletada = await self.secao_repository.delete(secao_id)
            if secao_deletada:
                return SecaoDTO.from_orm(secao_deletada)
            return None
        except HTTPException:
            raise  # repassa HTTPException já lançada (ex: de equipes ativas)
        except Exception as e:
            # Aqui você pode logar o erro detalhado, se desejar
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e) or "Não foi possível excluir a seção devido a dependências vinculadas."
            )

