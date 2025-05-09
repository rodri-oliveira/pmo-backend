from pydantic_settings import BaseSettings
from typing import Optional, List
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # Informações gerais da API
    PROJECT_NAME: str = "WEG Automação PMO"
    API_VERSION: str = "1.0.0"
    root_path: Optional[str] = None
    swagger_servers_list: Optional[str] = None
    
    # Configurações do banco de dados PostgreSQL da WEG
    DATABASE_URI: str = ""
    
    # Valores separados para uso interno
    DB_USER: str = "5e0dceda-d930-5742-a8d9-1f2d1ff22159"
    DB_PASSWORD: str = "b@p5rk8&9BJRVEQ"
    DB_HOST: str = "qas-postgresql-ap.weg.net"
    DB_PORT: str = "40030"
    DB_NAME: str = "automacaopmopostgre"
    
    # Segurança
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Configurações do Jira
    JIRA_BASE_URL: str = "https://your-domain.atlassian.net"
    JIRA_USERNAME: str = "your-jira-email@example.com"
    JIRA_API_TOKEN: str = "your-jira-api-token"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# Se DATABASE_URI não foi definido no .env, construa a string com URL encoding
if not settings.DATABASE_URI:
    password = quote_plus(settings.DB_PASSWORD)
    settings.DATABASE_URI = f"postgresql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

