from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Informações gerais da API
    PROJECT_NAME: str = "WEG Automação PMO"
    API_VERSION: str = "1.0.0"
    root_path: Optional[str] = None
    swagger_servers_list: Optional[str] = None
    
    # Configurações do banco de dados PostgreSQL da WEG
    DATABASE_URI: str = "postgresql://5e0dceda-d930-5742-a8d9-1f2d1ff22159:b@p5rk8&9BJRVEQ@qas-postgresql-ap.weg.net:40030/automacaopmopostgre"
    
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

settings = Settings()  # type: ignore