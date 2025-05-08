from fastapi import APIRouter, Depends

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Verifica o status da API")
def health_check():
    """
    Endpoint para verificação de saúde da API.
    
    Returns:
        dict: Status da API
    """
    return {"status": "ok"}

@router.get("/readiness", include_in_schema=False)
async def readiness():
    return { "status": "ok" };

@router.get("/liveness", include_in_schema=False)
async def liveness():
    return { "status": "ok" };
