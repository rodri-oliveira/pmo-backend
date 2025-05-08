from typing import Dict, List
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI) -> Dict:
    """
    Cria um schema OpenAPI personalizado com informações detalhadas sobre os endpoints da API.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="WEG Automação PMO API",
        version="1.0.0",
        description="""
        # Sistema de Gestão de Projetos e Melhorias

        Esta API fornece endpoints para gerenciar todos os aspectos do Sistema de Gestão de Projetos e Melhorias da WEG.
        
        ## Funcionalidades Principais:
        
        * Gerenciamento de seções, equipes, recursos e projetos
        * Planejamento e alocação de horas
        * Integração com Jira para sincronização de apontamentos
        * Relatórios e análises
        
        ## Autenticação:
        
        A API utiliza autenticação via token OAuth2. Todos os endpoints (exceto o webhook do Jira) requerem autenticação.
        """,
        routes=app.routes,
    )
    
    # Adiciona tags com descrições para melhor organização
    openapi_schema["tags"] = [
        {
            "name": "Administração",
            "description": "Endpoints para gerenciamento de usuários e configurações do sistema"
        },
        {
            "name": "Recursos Humanos",
            "description": "Endpoints para gerenciamento de recursos, equipes e seções"
        },
        {
            "name": "Projetos",
            "description": "Endpoints para gerenciamento de projetos e seus status"
        },
        {
            "name": "Alocações",
            "description": "Endpoints para gerenciar alocações de recursos em projetos"
        },
        {
            "name": "Apontamentos",
            "description": "Endpoints para registro e consulta de horas trabalhadas"
        },
        {
            "name": "Planejamento",
            "description": "Endpoints para planejamento de horas mensais por recurso/projeto"
        },
        {
            "name": "Relatórios",
            "description": "Endpoints para geração de relatórios e análises"
        },
        {
            "name": "Integração Jira",
            "description": "Endpoints para gerenciar a sincronização com o Jira"
        },
        {
            "name": "Sistema",
            "description": "Endpoints relacionados ao funcionamento do sistema"
        },
    ]
    
    # Adiciona componentes de segurança
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/backend/v1/auth/token",
                    "scopes": {}
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 