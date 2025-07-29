# Event Hub Local - Arquitetura Kafka com Proxy e Billing

Este projeto simula localmente uma arquitetura moderna de Hub de Eventos baseada em Apache Kafka, com proxy autenticado e controle de consumo (billing).

---

## 🚀 Visão Geral

A solução permite múltiplos tenants produzirem e consumirem eventos em tópicos isolados, com controle de acesso via OAuth2/JWT, persistência dos dados e métricas em PostgreSQL.

---

## 🎯 Requisitos Aplicados

### 1. Requisitos Funcionais

- Suporte a múltiplos tenants com tópicos dinâmicos e isolados por tenant.
- Produção e consumo de eventos via proxy autenticado.
- Autenticação e autorização via OAuth2/JWT no proxy.
- Registro detalhado do consumo por tenant, client e tópico para billing.
- Armazenamento persistente de logs e métricas em PostgreSQL.
- Escalabilidade horizontal para múltiplos tenants e conexões simultâneas.

### 2. Requisitos Não Funcionais

- Baixa latência e alta performance na comunicação proxy-Kafka.
- Persistência e resiliência dos dados e métricas.
- Segurança reforçada na autenticação e proteção dos dados.
- Portabilidade via Docker Compose para fácil deploy local ou nuvem.
- Automação de processos billing.

### 3. Requisitos Técnicos

- Apache Kafka 7.5.0 e Zookeeper compatível.
- PostgreSQL 15 para persistência de métricas e billing.
- Proxy em Python (Flask/FastAPI) com integração Kafka e OAuth2.
- Scripts auxiliares para automação de tarefas.

### 4. Requisitos de Integração

- Proxy integra com Kafka via confluent-kafka-python.
- Proxy registra schemas via REST API do Schema Registry.
- Proxy armazena logs e billing no PostgreSQL.
- Suporte para múltiplos tenants com namespace isolado.
- Identificação do client produtor e consumidor

### 5. Requisitos de Uso

- Acesso ao proxy via tokens OAuth2/JWT válidos.
- Produção e consumo com identificação clara do tenant e client.
- Billing gerado automaticamente a partir dos logs de consumo.
- Administração Kafka via Kafka UI (opcional).

---

## 📦 Estrutura do Projeto

```
event-hub-local/
│
├── docker-compose.yml           # Orquestração dos serviços
├── proxy/                      # Código do proxy Python
│   ├── app.py
│   ├── auth.py
│   ├── billing.py
│   ├── kafka_client.py
│   └── requirements.txt
├── schema/
│   └── register_schemas.py     # Script para registrar schemas automaticamente
├── grafana/
│   └── dashboards/             # Dashboards prontos para Grafana
├── prometheus/
│   └── prometheus.yml          # Configuração do Prometheus
├── postgres/
│   └── init.sql                # Script para criação das tabelas de billing
└── redis/                      # Configurações padrões do Redis (Docker)
```

---

## ⚙️ Como Rodar Localmente

1. Clone o repositório.

2. Execute o comando abaixo para subir os serviços:

```bash
docker-compose up --build
```

3. Acesse os serviços:

- Kafka Broker: `localhost:9092`
- Schema Registry: `http://localhost:8081`
- Proxy API: `http://localhost:5000`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (usuário/senha padrão: admin/admin)

4. Registre schemas automaticamente executando:

```bash
python3 schema/register_schemas.py
```

5. Teste a produção e consumo via proxy usando um token OAuth2/JWT válido.

---

## 🧪 Testes com `curl`

### Obter token:

```bash
curl -X POST http://localhost:5000/token \
-H "Content-Type: application/json" \
-d '{"user":"usuario_teste","tenant":"tenant1"}'
```

### Enviar evento de produção:

```bash
curl -X POST http://localhost:5000/produce \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "topic": "topic1",
  "client_id":"producer_app_1",
  "message": {"key":"teste", "value": 123}
}'
```

### Enviar evento de consumo:

```bash
curl -X GET "http://localhost:5000/consume?topic=topic1&client_id=consumer_app_1" \
-H "Authorization: Bearer <TOKEN>"
```

### Enviar evento de consumo iniciando no offset especificado (com start_offset):

```bash
curl -X GET "http://localhost:5000/consume?topic=topic1&client_id=consumer_app_1&start_offset=0" \
-H "Authorization: Bearer <TOKEN>"
```

### Enviar evento de consumo iniciando no start_time especificado (por timestamp):

```bash
curl -X GET "http://localhost:5000/consume?topic=topic1&client_id=consumer_app_1&start_time=2025-07-28T14:00:00Z" \
-H "Authorization: Bearer <TOKEN>"
```

## 🧾 Estrutura da Tabela `billing`

```sql
CREATE TABLE IF NOT EXISTS billing (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    client_id VARCHAR(255) NOT NULL,
    mensagens INTEGER NOT NULL,
    bytes INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    event_time TIMESTAMP NOT NULL
);
```

## 💡 Observações

- O campo `client_id` permite registrar quem está produzindo ou consumindo as mensagens.
- `action` define se foi uma operação de `produce` ou `consume`.

## Sugestão de cálculo de custo
- Custo por mensagem: R$ 0,005
- Custo por byte: R$ 0,00001
```bash
SELECT
  client_id,
  SUM(mensagens) AS total_mensagens,
  SUM(bytes) AS total_bytes,
  SUM(mensagens)*0.005 AS custo_mensagens,
  SUM(bytes)*0.00001 AS custo_bytes,
  SUM(mensagens)*0.005 + SUM(bytes)*0.00001 AS custo_total
FROM billing
GROUP BY client_id
ORDER BY client_id;
```

## 📊 Monitoramento e Billing

- O proxy expõe métricas no formato Prometheus.
- Grafana está configurado para mostrar dashboards de métricas por tenant e tópico.
- Billing é gerado automaticamente a partir dos logs de consumo gravados no PostgreSQL.

---

## 🔐 Segurança

- O proxy exige token JWT válido para todas as operações.
- Dados são isolados por tenant para garantir segurança multi-tenant.
- Variáveis sensíveis são configuradas via ambiente (é recomendado usar Docker secrets para produção).

---

## 📚 Referências

- [Apache Kafka](https://kafka.apache.org/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [OAuth2 & JWT](https://oauth.net/2/)
- [Redis](https://redis.io/)
- [PostgreSQL](https://www.postgresql.org/)

---

## 🤝 Contribuições

Contribuições são bem-vindas! Abra issues ou pull requests para melhorias.

---

**Desenvolvido para fornecer uma arquitetura escalável e segura para hub de eventos multi-tenant com Kafka e monitoramento completo.**

