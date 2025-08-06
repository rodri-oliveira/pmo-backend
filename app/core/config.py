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
    
    # Valores separados para uso interno (lidos do .env)
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = ""
    DB_NAME: str = ""
    
    # Segurança (lidos do .env)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Auth (lidos do .env)
    auth_keycloak_id: str = ""
    auth_keycloak_secret: str = ""
    auth_secret: str = ""
    nextauth_url: str = ""
    auth_keycloak_issuer: str = ""
    nextauth_secret: str = ""
    next_public_backend_url: str = ""
    
    # CORS
    # Allowed origins for CORS – include frontend dev servers
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:8000",
        "https://automacao-pmo-qas.weg.net"
    ]
    
    # Configurações do Jira (lidos do .env)
    JIRA_BASE_URL: str = ""  # URL base do Jira Cloud
    JIRA_USERNAME: str = ""  # E-mail do usuário com permissão de API
    JIRA_API_TOKEN: str = ""  # Token de API gerado no Jira
    # A URL da API pode ser montada dinamicamente como f"{JIRA_BASE_URL}/rest/api/3"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"  # Não permite variáveis extras para segurança

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATABASE_URI = f"postgresql+asyncpg://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()

# Defina a URL de conexão diretamente nas configurações do contexto
def get_url():
    return settings.DATABASE_URI
