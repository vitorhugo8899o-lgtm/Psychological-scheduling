<div align="center">
  <img width="1408" height="670" alt="Logo-software-png" src="https://github.com/user-attachments/assets/ee234c81-5dce-49df-b4c5-1ebc5810f3ff" />
</div>

# MentalHealing Software (Backend)

O **MentalHealing Software** é uma plataforma desenvolvida para facilitar o agendamento e a gestão de consultas com profissionais da área da saúde mental. Por meio do sistema, os usuários podem encontrar profissionais e agendar consultas de forma prática, rápida e segura.

Além disso, a plataforma oferece recursos completos para os profissionais, permitindo o gerenciamento de horários de atendimento, consultas agendadas, métricas de desempenho e acompanhamento da rotina clínica.

O sistema também conta com um módulo administrativo voltado para a gestão da clínica, possibilitando o cadastro de novos psicólogos, controle de relatórios financeiros, gerenciamento de perfis, desativação de contas e administração geral da plataforma.

---

---
<br/>

## Arquitetura

A aplicação frontend se comunica com a API backend via HTTP, seguindo o modelo:

```
┌─────────────────────────┐
│     Frontend (React)    │
│    (Este repositório)   │
└────────────┬────────────┘
             │
             │ HTTP Requests (com cookies)
             ▼
┌─────────────────────────┐
│   Redis (Rate Limit)    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐               SERVIÇOS EXTERNOS
│     FastAPI Backend     │       ┌─────────────────────────────────┐
│        (API REST)       ├──────►│ Mercado Pago (Gateway de Pag.)  │
└────────────┬────────────┘       └─────────────────────────────────┘
             │                    ┌─────────────────────────────────┐
             ├───────────────────►│       GROQ (Agente de IA)       │
             │                    └─────────────────────────────────┘
             ▼
┌─────────────────────────┐
│      Redis (Cache)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     Banco de Dados      │
│      (PostgreSQL)       │
└─────────────────────────┘
```

* Comunicação baseada em **requisições HTTP com autenticação via cookies**
* Separação clara entre camada de apresentação (frontend) e lógica de negócio (backend)


---

---

| Tecnologia | Finalidade |
| :--- | :--- |
| **Python + FastAPI** | Framework principal utilizado para construção da API REST assíncrona |
| **SQLAlchemy** | ORM responsável pelo mapeamento e manipulação do banco de dados |
| **Alembic** | Ferramenta de versionamento e controle de migrações do banco |
| **PostgreSQL + asyncpg** | Banco de dados relacional com driver assíncrono de alta performance |
| **Redis** | Sistema de cache e controle de Rate Limit |
| **SlowAPI** | Gerenciamento e orquestração de limite de requisições (Rate Limiting) |
| **Argon2** | Algoritmo seguro para criptografia e hash de senhas |
| **Docker** | Containerização e padronização do ambiente da aplicação |
| **Pytest** | Estrutura para criação e execução de testes automatizados |
| **Mercado Pago SDK** | Integração com gateway de pagamento em ambiente Sandbox |
| **Groq API** | Comunicação e processamento com o agente de Inteligência Artificial |
| **RapidFuzz** | Comparação inteligente de textos e busca aproximada em FAQs do sistema |


---
