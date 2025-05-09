from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Informações gerais da API
    PROJECT_NAME: str = "WEG Automação PMO"
    API_VERSION: str = "1.0.0"
    root_path: Optional[str] = None
    swagger_servers_list: Optional[str] = None
<<<<<<< HEAD
    
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
    
=======

    # PostgreSQL Database Configuration
    POSTGRES_USER: str = "user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "appdb"
    DATABASE_URL: Optional[str] = None

    def __init__(self, **values):
        super().__init__(**values)
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

>>>>>>> 00dfbfaffe36b844d48fa90831148ec7ad9b9d9d
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() # type: ignore

