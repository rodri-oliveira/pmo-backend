import asyncio
import asyncpg
from urllib.parse import quote_plus

# Configurações do banco de dados
DB_USER = "5e0dceda-d930-5742-a8d9-1f2d1ff22159"
DB_PASSWORD = "b@p5rk8&9BJRVEQ"
DB_HOST = "qas-postgresql-ap.weg.net"
DB_PORT = "40030"
DB_NAME = "automacaopmopostgre"

async def test_connection():
    print("Testando conexão com o PostgreSQL usando asyncpg...")
    
    # Codificar a senha para URL
    password = quote_plus(DB_PASSWORD)
    
    # Criar string de conexão no formato que o asyncpg espera
    # Nota: asyncpg usa um formato diferente do SQLAlchemy
    dsn = f"postgres://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        # Tentar estabelecer uma conexão
        conn = await asyncpg.connect(dsn)
        print("Conexão estabelecida com sucesso!")
        
        # Executar uma consulta simples
        version = await conn.fetchval("SELECT version()")
        print(f"Versão do PostgreSQL: {version}")
        
        # Fechar a conexão
        await conn.close()
        print("Conexão fechada.")
        
        # Se chegou até aqui, o driver está funcionando
        print("\nO driver asyncpg está instalado e funcionando corretamente!")
        
        # Agora vamos mostrar como configurar o SQLAlchemy com asyncpg
        print("\nPara configurar o SQLAlchemy com asyncpg, use:")
        print(f"DATABASE_URI = \"postgresql+asyncpg://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}\"")
        
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        print("\nVerifique se:")
        print("1. O pacote asyncpg está instalado corretamente (pip install asyncpg)")
        print("2. As credenciais do banco de dados estão corretas")
        print("3. O servidor PostgreSQL está acessível a partir desta máquina")
        print("4. O firewall não está bloqueando a conexão")

if __name__ == "__main__":
    # Executar o teste de conexão
    asyncio.run(test_connection())
