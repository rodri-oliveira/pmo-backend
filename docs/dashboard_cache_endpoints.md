# Dashboard Cache - Endpoints para Frontend

## 📋 Visão Geral

Este documento descreve os endpoints otimizados para consumo do frontend, que utilizam dados da tabela `dashboard_jira_snapshot` para garantir performance e disponibilidade imediata dos dashboards Jira.

## 🎯 Arquitetura

### **Estratégia de Cache:**
- **Tabela dedicada:** `dashboard_jira_snapshot` armazena dados pré-processados
- **Sincronização periódica:** Popula cache com dados do Jira usando JQLs específicos
- **Performance otimizada:** Frontend consome dados locais instantaneamente
- **Flexibilidade:** Permite sincronização manual e automática

### **JQLs Implementados:**
- **DTIN:** Demandas, Melhorias e Recursos Alocados com filtros específicos
- **SEG:** Projetos de Segurança da Informação com exclusões customizadas  
- **SGI:** Suporte Global Infraestrutura com assignees hardcoded

## 🔧 Endpoints Disponíveis

### **1. Status do Cache**
```http
GET /backend/dashboard-cache/status
```

**Descrição:** Retorna status atual do cache por seção, incluindo última sincronização e disponibilidade dos dados.

**Resposta:**
```json
{
  "timestamp": "2025-08-04T09:47:26.072616",
  "secoes": {
    "DTIN": {
      "disponivel": true,
      "ultima_sincronizacao": "2025-08-04T08:30:15",
      "registros": 1250,
      "idade_horas": 1.2,
      "dashboards": ["demandas", "melhorias", "recursos_alocados"]
    },
    "SEG": {
      "disponivel": true,
      "ultima_sincronizacao": "2025-08-04T08:30:20", 
      "registros": 890,
      "idade_horas": 1.2,
      "dashboards": ["demandas", "melhorias", "recursos_alocados"]
    },
    "SGI": {
      "disponivel": true,
      "ultima_sincronizacao": "2025-08-04T08:30:25",
      "registros": 1100,
      "idade_horas": 1.2,
      "dashboards": ["demandas", "melhorias", "recursos_alocados"]
    }
  },
  "cache_ativo": true
}
```

### **2. Sincronização Flexível**
```http
POST /backend/dashboard-cache/sync
```

**Descrição:** Executa sincronização do cache com filtros flexíveis de data e seções.

**Request Body:**
```json
{
  "data_inicio": "2025-01-01",
  "data_fim": "2025-12-31",
  "secoes": ["DTIN", "SEG", "SGI"],
  "force_refresh": false
}
```

**Parâmetros:**
- `data_inicio` *(obrigatório)*: Data início no formato YYYY-MM-DD
- `data_fim` *(obrigatório)*: Data fim no formato YYYY-MM-DD  
- `secoes` *(opcional)*: Lista de seções específicas. Default: todas ["DTIN", "SEG", "SGI"]
- `force_refresh` *(opcional)*: Forçar refresh mesmo se dados existem. Default: false

**Resposta:**
```json
{
  "status": "completed",
  "periodo": "2025-01-01 a 2025-12-31",
  "tempo_total_segundos": 31.5,
  "timestamp": "2025-08-04T09:49:49.119026",
  "resultados": {
    "DTIN": {
      "status": "success",
      "registros": 1250,
      "tempo_segundos": 10.2,
      "ultima_sincronizacao": "2025-08-04T09:49:38",
      "erro": null
    },
    "SEG": {
      "status": "success", 
      "registros": 890,
      "tempo_segundos": 8.5,
      "ultima_sincronizacao": "2025-08-04T09:49:46",
      "erro": null
    },
    "SGI": {
      "status": "success",
      "registros": 1100, 
      "tempo_segundos": 12.8,
      "ultima_sincronizacao": "2025-08-04T09:49:49",
      "erro": null
    }
  }
}
```

## 📊 Dados do Cache

### **Estrutura da Tabela `dashboard_jira_snapshot`:**
```sql
CREATE TABLE dashboard_jira_snapshot (
    id SERIAL PRIMARY KEY,
    secao VARCHAR(10) NOT NULL,
    dashboard_tipo VARCHAR(50) NOT NULL,
    status_nome VARCHAR(100) NOT NULL,
    quantidade INTEGER NOT NULL DEFAULT 0,
    data_snapshot TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    filtros_aplicados JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Tipos de Dashboard:**
- `demandas`: Issues do tipo Epic com labels específicos por seção
- `melhorias`: Issues de melhoria e rotinas por seção
- `recursos_alocados`: Issues atribuídas a recursos específicos por seção

## 🔄 Fluxo de Sincronização

### **1. Validação:**
- Formato das datas (YYYY-MM-DD)
- Seções válidas (DTIN, SEG, SGI)
- Data início < Data fim

### **2. Execução por Seção:**
- Construção de JQLs específicos por seção e tipo de dashboard
- Busca paginada no Jira (máximo 1000 issues por consulta)
- Processamento e agregação dos dados
- Salvamento incremental na tabela cache

### **3. Resposta Detalhada:**
- Status por seção (success/error)
- Tempo de execução individual
- Quantidade de registros processados
- Erros específicos se houver

## ⚡ Performance

### **Otimizações Implementadas:**
- **Limite de volume:** Máximo 1000 issues por consulta para evitar timeout
- **Salvamento incremental:** Dados salvos em lotes durante processamento
- **Cache local:** Frontend consome dados da tabela local instantaneamente
- **Sincronização assíncrona:** Não bloqueia outras operações

### **Tempos Típicos:**
- **DTIN:** ~10-15 segundos (1200+ registros)
- **SEG:** ~8-12 segundos (800+ registros)  
- **SGI:** ~10-15 segundos (1000+ registros)
- **Total:** ~30-40 segundos para todas as seções

## 🚨 Tratamento de Erros

### **Códigos de Status HTTP:**
- `200`: Sucesso
- `400`: Erro de validação (datas, seções inválidas)
- `500`: Erro interno (Jira indisponível, erro de banco)

### **Erros Comuns:**
```json
{
  "detail": "Formato de data inválido: time data '2025-13-01' does not match format '%Y-%m-%d'"
}
```

```json
{
  "detail": "Seções inválidas: ['INVALID']. Válidas: ['DTIN', 'SEG', 'SGI']"
}
```

```json
{
  "detail": "Data início deve ser menor que data fim"
}
```

## 🔧 Uso Recomendado

### **Para Frontend:**
1. **Verificar status** do cache antes de solicitar dados
2. **Sincronizar** se dados estão desatualizados (>24h)
3. **Consumir dados** da tabela local para renderização rápida
4. **Monitorar erros** e implementar fallbacks

### **Exemplo de Integração:**
```javascript
// 1. Verificar status do cache
const status = await fetch('/backend/dashboard-cache/status');
const cacheInfo = await status.json();

// 2. Sincronizar se necessário
if (cacheInfo.secoes.DTIN.idade_horas > 24) {
  const sync = await fetch('/backend/dashboard-cache/sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      data_inicio: '2025-01-01',
      data_fim: '2025-12-31',
      secoes: ['DTIN'],
      force_refresh: false
    })
  });
  const result = await sync.json();
  console.log('Sincronização:', result.status);
}

// 3. Consumir dados do cache (endpoints existentes)
const dashboardData = await fetch('/backend/v1/dashboard-jira/demandas?secao=DTIN');
```

## 📝 Logs e Monitoramento

### **Logs Disponíveis:**
- Início e fim de sincronização por seção
- Tempos de execução detalhados
- Quantidade de registros processados
- Erros específicos com stack trace

### **Exemplo de Log:**
```
2025-08-04 09:49:38 [INFO] Iniciando sincronização: DTIN (2025-01-01 a 2025-12-31)
2025-08-04 09:49:45 [INFO] DTIN demandas: 450 registros processados
2025-08-04 09:49:47 [INFO] DTIN melhorias: 380 registros processados  
2025-08-04 09:49:48 [INFO] DTIN recursos: 420 registros processados
2025-08-04 09:49:48 [INFO] DTIN concluída: 1250 registros em 10.2s
```

## 🔒 Segurança

### **Autenticação:**
- Endpoints protegidos por autenticação da aplicação
- Validação de permissões por seção se necessário

### **Validação:**
- Sanitização de parâmetros de entrada
- Validação rigorosa de datas e seções
- Proteção contra SQL injection via ORM

## 📚 Referências

- **Tabela Cache:** `dashboard_jira_snapshot`
- **Serviços:** `DashboardJiraSyncService`, `DashboardJiraQueryService`
- **JQLs:** Definidos em `DashboardJiraService` por seção
- **Endpoints Legados:** `/backend/v1/dashboard-jira/*` (consulta direta ao Jira)
