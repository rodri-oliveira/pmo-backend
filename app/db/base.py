# Importar todos os modelos para que o Alembic os reconheça
from app.db.session import Base
from app.db.orm_models import Secao, Equipe, Recurso, StatusProjeto, Projeto, AlocacaoRecursoProjeto, HorasDisponiveisRH, HorasPlanejadas, Apontamento, Usuario, Configuracao, LogAtividade, SincronizacaoJira, DimTempo 