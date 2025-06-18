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

    async def get_all_status_projetos(self, skip: int = 0, limit: int = 100, ativo: Optional[bool] = None) -> List[StatusProjetoDTO]:
        status_projetos = await self.status_projeto_repository.get_all(skip=skip, limit=limit, ativo=ativo)
        return [StatusProjetoDTO.from_orm(sp) for sp in status_projetos]

    async def create_status_projeto(self, status_create_dto: StatusProjetoCreateDTO) -> StatusProjetoDTO:
        # 1. Checar por nome (para possível reativação)
        status_existente_por_nome = await self.status_projeto_repository.get_by_nome_including_inactive(status_create_dto.nome)

        # 2. Checar por ordem de exibição, se fornecida
        if status_create_dto.ordem_exibicao is not None:
            status_existente_por_ordem = await self.status_projeto_repository.get_by_ordem_exibicao_including_inactive(status_create_dto.ordem_exibicao)
            # Se a ordem já existe E pertence a um status DIFERENTE do que estamos tentando reativar pelo nome
            if status_existente_por_ordem and (status_existente_por_nome is None or status_existente_por_ordem.id != status_existente_por_nome.id):
                    raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A ordem de exibição '{status_create_dto.ordem_exibicao}' já está em uso por outro status."
                )

        # 3. Lógica de reativação ou criação
        if status_existente_por_nome:
            if not status_existente_por_nome.ativo:
                # Reativar
                update_dto = StatusProjetoUpdateDTO(
                    nome=status_create_dto.nome,
                    descricao=status_create_dto.descricao,
                    is_final=status_create_dto.is_final,
                    # Usa a nova ordem se fornecida, senão mantém a antiga. A validação já foi feita.
                    ordem_exibicao=status_create_dto.ordem_exibicao or status_existente_por_nome.ordem_exibicao,
                    ativo=True
                )
                status_atualizado = await self.status_projeto_repository.update(status_existente_por_nome.id, update_dto)
                return StatusProjetoDTO.from_orm(status_atualizado)
            else:
                # Nome duplicado em status ativo
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Já existe um status de projeto ativo com o nome '{status_create_dto.nome}'."
                )

        # 4. Se chegou aqui, é uma criação nova.
        # Se a ordem não foi fornecida, calcular uma que esteja vaga.
        if status_create_dto.ordem_exibicao is None:
            max_order = await self.status_projeto_repository.get_max_ordem_exibicao()
            new_order = (max_order or 0) + 1
            # Loop para garantir que a nova ordem não colida com um item inativo
            while await self.status_projeto_repository.get_by_ordem_exibicao_including_inactive(new_order):
                new_order += 1
            status_create_dto.ordem_exibicao = new_order

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

