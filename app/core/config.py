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

    # Auth
    auth_keycloak_id: str = ""
    auth_keycloak_secret: str = ""
    auth_secret: str = ""
    nextauth_url: str = ""
    auth_keycloak_issuer: str = ""
    nextauth_secret: str = ""
    next_public_backend_url: str = ""
    
    # CORS
    # Allowed origins for CORS – include frontend dev servers
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:8000"]
    
    # Configurações do Jira
    JIRA_BASE_URL: str = "https://jiracloudweg.atlassian.net"  # URL base do Jira Cloud
    JIRA_USERNAME: str = "roliveira@weg.net"  # E-mail do usuário com permissão de API
    JIRA_API_TOKEN: str = "cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF"  # Token de API gerado no Jira
    # A URL da API pode ser montada dinamicamente como f"{JIRA_BASE_URL}/rest/api/3"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"  # Não permite variáveis extras para segurança

settings = Settings()

# String de conexão para o banco de dados
from urllib.parse import quote_plus
password = quote_plus(settings.DB_PASSWORD)
settings.DATABASE_URI = f"postgresql+asyncpg://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
print(f"--- CONECTANDO AO BANCO: {settings.DATABASE_URI} ---")

# Defina a URL de conexão diretamente nas configurações do contexto
def get_url():
    return settings.DATABASE_URI
