from sqlalchemy.orm import Query
from sqlalchemy import or_, func

def apply_search_filter(query: Query, model, search: str, fields=None):
    """
    Aplica filtro de busca case-insensitive em múltiplos campos de um modelo SQLAlchemy.
    Args:
        query: Query SQLAlchemy
        model: Modelo SQLAlchemy
        search: termo de busca
        fields: lista de campos do modelo a buscar (ex: [Model.nome, Model.email])
    Returns:
        Query filtrada
    """
    if not search or not fields:
        return query
    search = search.strip().lower()
    filters = [func.lower(getattr(model, field.key)).like(f"%{search}%") for field in fields]
    return query.filter(or_(*filters))
