import sys
import logging
from sqlalchemy import create_engine, text
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_connection():
    """Testar a conexão com o banco de dados PostgreSQL."""
    try:
        # Criar engine de conexão com o PostgreSQL
        engine = create_engine(settings.DATABASE_URI)
        
        # Testar conexão executando uma consulta simples
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            for row in result:
                logger.info(f"Conexão bem-sucedida: {row}")
            
        logger.info("Conexão com o banco de dados PostgreSQL estabelecida com sucesso!")
        return True
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 