from datetime import datetime, date
from fastapi import HTTPException

def parse_date_flex(value):
    """
    Converte uma string de data nos formatos 'YYYY-MM-DD' ou 'DD/MM/YYYY' para um objeto date.
    Aceita também objetos date ou datetime, retornando sempre date.
    Lança HTTPException 422 se o formato for inválido.
    """
    if value is None or isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(value, "%d/%m/%Y").date()
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Formato de data inválido: {value}. Use YYYY-MM-DD ou DD/MM/YYYY."
                )
    return value
