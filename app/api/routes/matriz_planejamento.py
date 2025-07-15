from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database_config import get_db
from app.core.security import get_current_admin_user
from app.models.usuario import Usuario
from app.schemas.matriz_planejamento_schemas import MatrizPlanejamentoUpdate
from app.services.planejamento_horas_service import PlanejamentoHorasService

router = APIRouter()

@router.post("/salvar",
             summary="Salva as alterações da matriz de planejamento",
             description="Recebe todas as modificações de status, esforço, observação e horas planejadas para um recurso em um determinado ano e as salva no banco de dados.",
             response_model=dict)
async def salvar_matriz_planejamento(
    payload: MatrizPlanejamentoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_admin_user)
):
    """
    Endpoint para salvar em lote as alterações da matriz de planejamento.

    - **recurso_id**: ID do recurso sendo planejado.
    - **ano**: Ano de referência do planejamento.
    - **alteracoes_projetos**: Lista de projetos com suas respectivas alterações.
        - **projeto_id**: ID do projeto.
        - **status_alocacao_id**: Novo status da alocação.
        - **observacao**: Nova observação/ação.
        - **esforco_estimado**: Novo esforço estimado em horas.
        - **planejamento_mensal**: Lista de horas planejadas por mês.
    """
    try:
        service = PlanejamentoHorasService(db)
        await service.salvar_alteracoes_matriz(payload)
        return {"message": "Matriz de planejamento salva com sucesso!"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Idealmente, logar o erro aqui
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado ao salvar a matriz: {str(e)}")
