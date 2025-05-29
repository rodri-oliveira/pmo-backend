import requests
import json

# Token Base64 fornecido pelo usuário
auth_header = "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF"

# URL do Jira
url = "https://jiracloudweg.atlassian.net/rest/api/3/project/search"

# Cabeçalhos com o header de autorização
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": auth_header
}

print("Testando conexão com o Jira...")
print(f"URL: {url}")
print(f"Headers: {headers}")

try:
    # Fazer requisição GET
    response = requests.get(url, headers=headers)
    
    # Verificar status code
    print(f"Status code: {response.status_code}")
    
    # Se a resposta for bem-sucedida, imprimir os dados
    if response.status_code == 200:
        data = response.json()
        print(f"Resposta bem-sucedida! Total de projetos: {data.get('total', 'N/A')}")
        
        # Verificar se há valores na resposta
        values = data.get('values', [])
        print(f"Número de projetos retornados: {len(values)}")
        
        # Imprimir os primeiros 3 projetos
        if values:
            print("\nPrimeiros 3 projetos:")
            for i, project in enumerate(values[:3]):
                print(f"{i+1}. {project.get('key')} - {project.get('name')}")
    else:
        print(f"Erro na requisição: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except Exception as e:
    print(f"Erro ao conectar com o Jira: {str(e)}")
