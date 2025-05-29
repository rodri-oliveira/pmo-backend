import requests
import json
from datetime import datetime, timedelta

# Token Base64 fornecido pelo usuário
auth_header = "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF"

# URL base do Jira
base_url = "https://jiracloudweg.atlassian.net"

# Cabeçalhos com o header de autorização
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": auth_header
}

# Calcular a data de início para a busca (últimos 30 dias)
start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

# JQL para buscar issues com worklogs no período
jql = f"worklogDate >= {start_date} ORDER BY updated DESC"

# URL para buscar issues com worklogs
search_url = f"{base_url}/rest/api/3/search"

# Parâmetros da busca
params = {
    "jql": jql,
    "fields": "key,summary",
    "maxResults": 100
}

print(f"Buscando issues com worklogs desde {start_date}...")
print(f"JQL: {jql}")

try:
    # Fazer requisição para buscar issues
    response = requests.get(search_url, headers=headers, params=params)
    
    # Verificar status code
    print(f"Status code: {response.status_code}")
    
    # Se a resposta for bem-sucedida, processar as issues
    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        print(f"Encontradas {len(issues)} issues com worklogs")
        
        # Buscar worklogs para cada issue
        all_worklogs = []
        
        for issue in issues[:5]:  # Limitar a 5 issues para teste
            issue_key = issue.get("key")
            if not issue_key:
                continue
                
            print(f"\nBuscando worklogs da issue {issue_key}...")
            
            # URL para buscar worklogs da issue
            worklog_url = f"{base_url}/rest/api/3/issue/{issue_key}/worklog"
            
            # Fazer requisição para buscar worklogs
            worklog_response = requests.get(worklog_url, headers=headers)
            
            # Verificar status code
            print(f"Status code: {worklog_response.status_code}")
            
            # Se a resposta for bem-sucedida, processar os worklogs
            if worklog_response.status_code == 200:
                worklog_data = worklog_response.json()
                worklogs = worklog_data.get("worklogs", [])
                print(f"Encontrados {len(worklogs)} worklogs na issue {issue_key}")
                
                # Adicionar informações da issue aos worklogs
                for worklog in worklogs:
                    worklog["issueKey"] = issue_key
                    worklog["issueSummary"] = issue.get("fields", {}).get("summary", "")
                    all_worklogs.append(worklog)
            else:
                print(f"Erro ao buscar worklogs da issue {issue_key}: {worklog_response.text}")
        
        print(f"\nTotal de worklogs encontrados: {len(all_worklogs)}")
        
        # Mostrar detalhes dos primeiros 3 worklogs
        if all_worklogs:
            print("\nDetalhes dos primeiros 3 worklogs:")
            for i, worklog in enumerate(all_worklogs[:3]):
                print(f"\n{i+1}. Worklog ID: {worklog.get('id')}")
                print(f"   Issue: {worklog.get('issueKey')} - {worklog.get('issueSummary')}")
                print(f"   Autor: {worklog.get('author', {}).get('displayName', 'N/A')}")
                print(f"   Data: {worklog.get('started', 'N/A')}")
                print(f"   Tempo gasto: {worklog.get('timeSpent', 'N/A')}")
                print(f"   Comentário: {worklog.get('comment', 'N/A')}")
    else:
        print(f"Erro na requisição: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except Exception as e:
    print(f"Erro ao conectar com o Jira: {str(e)}")
