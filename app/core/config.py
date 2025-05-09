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
    # Valores separados para facilitar a manipulação
    DB_USER: str = "5e0dceda-d930-5742-a8d9-1f2d1ff22159"
    DB_PASSWORD: str = "b@p5rk8&9BJRVEQ"
    DB_HOST: str = "qas-postgresql-ap.weg.net"
    DB_PORT: str = "40030"
    DB_NAME: str = "automacaopmopostgre"
    
    # Compõe a string de conexão usando URL encoding para a senha
    @property
    def DATABASE_URI(self) -> str:
        password = quote_plus(self.DB_PASSWORD)
        return f"postgresql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
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

