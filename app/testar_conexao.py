import psycopg2

print("Iniciando teste de conexão...")

# Dados de conexão
username = "5e0dceda-d930-5742-a8d9-1f2d1ff22159"
password = "b@p5rk8&9BJRVEQ"
host = "qas-postgresql-ap.weg.net"
port = "40030"
database = "automacaopmopostgre"

print(f"Tentando conectar a {host}:{port}/{database} com usuário {username}")

try:
    # Tenta conectar ao PostgreSQL
    conn = psycopg2.connect(
        dbname=database,
        user=username,
        password=password,
        host=host,
        port=port
    )
    
    print("SUCESSO: Conexão estabelecida!")
    
    # Testa a conexão com uma consulta simples
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    print(f"Resultado da consulta: {result}")
    
    # Fecha recursos
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"ERRO: Falha na conexão: {e}")
