<div align="center">
  <img width="1408" height="670" alt="Logo-software-png" src="https://github.com/user-attachments/assets/ee234c81-5dce-49df-b4c5-1ebc5810f3ff" />
</div>

# MentalHealing Software (Backend)

O **MentalHealing Software** é uma plataforma desenvolvida para facilitar o agendamento e a gestão de consultas com profissionais da área da saúde mental. Por meio do sistema, os usuários podem encontrar profissionais e agendar consultas de forma prática, rápida e segura.

Além disso, a plataforma oferece recursos completos para os profissionais, permitindo o gerenciamento de horários de atendimento, consultas agendadas, métricas de desempenho e acompanhamento da rotina clínica.

O sistema também conta com um módulo administrativo voltado para a gestão da clínica, possibilitando o cadastro de novos psicólogos, controle de relatórios financeiros, gerenciamento de perfis, desativação de contas e administração geral da plataforma.

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

<br/>

## Estrutura de pastas

```
  raiz-do-projeto/
├── 📂 app/                         # Código principal da aplicação
│   ├── 📂 api/                     # Módulos de comunicação externa (HTTP/REST)
│   │   └── 📂 v1/                  # Versão 1 da API
│   │       ├── 📂 endpoints/       # Rotas da API (Controllers)
│   │       ├── 📂 repositories/    # Camada de acesso ao banco de dados (Consultas)
│   │       ├── 📂 services/        # Camada de regras de negócio
│   │       ├── 📂 util/            # Funções utilitárias e helpers específicos da API
│   │       ├── 📄 dependencies.py  # Injeção de dependências do FastAPI (ex: autenticação, DB)
│   │       └── 📄 router.py        # Centralizador de rotas da v1
│   ├── 📂 core/                    # Configurações globais do sistema, segurança (JWT).
│   ├── 📂 db/                      # Inicialização do banco de dados e sessão do ORM
│   ├── 📂 groq/                    # Integração com o provedor de IA (Groq Cloud SDK), FAQ, cache de respotas no redis
│   ├── 📂 models/                  # Modelos do banco de dados (tabelas SQLAlchemy/SQLModel)
│   ├── 📂 redis/                   # Configurações e conexões do cache Redis
│   ├── 📂 schemas/                 # Modelos de validação de dados (Pydantic)
│   └── 📄 main.py                  # Ponto de entrada (Bootstrap) do FastAPI
├── 📂 migrations/                  # Histórico de migrações do banco de dados (Alembic)
├── 📂 tests/                       # Testes automatizados (Unitários e de Integração)
├── 📄 .dockerignore                # Arquivos ignorados no build do Docker
├── 📄 .env                         # Variáveis de ambiente (exemplo local)
├── 📄 .gitignore                   # Arquivos ignorados pelo Git
├── 📄 alembic.ini                  # Configurações da ferramenta de migração
├── 📄 Dockerfile                   # Instruções para containerização do app
├── 📄 poetry.lock                  # Versões exatas das dependências (Poetry)
└── 📄 pyproject.toml               # Configuração do projeto e dependências Python
```

---

# Tech Stack

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

##  Endpoints

###  Users

* `POST /api/v1/users` → Criação de usuário
* `PUT /api/v1/users` → Atualizar informações do usuário
* `DELETE /api/v1/users` → Desativar usuário
* `POST /api/v1/login` → Logar usuário
* `POST /api/v1/logout` → Deslogar usuário
* `GET /api/v1/users` → Busca todos os usuários criados
* `GET /api/v1/users/{id_user}` → Busca informação de um usuário específico
* `GET /api/v1/users/me/appointments` → Busca todas as consultas de um usuário
* `GET /api/v1/users/me/next-appoiments` → Busca as proxímas 3 consultas confirmadas
* `POST /api/v1/validate-session` → Valida se o usuário está logado
* `GET /api/v1/users/me/open-appoiments` → Busca todas as consultas com o status pedding(aberto) do dia atual para frente

###  Adm

* `POST /api/v1/psychologist` → Adiciona um psicólogo ao sistema
* `POST /api/v1/services` → Adiciona um serviço oferecido pela clinica
* `POST /api/v1/financial-report` → Devolve um relátorio financeiro com base em uma data definida

### Services

* `GET /api/v1/services` → Busca todos os serviços cadastrados no sistema
* `GET /api/v1/services/{service_id}` → Busca um serviço específico
* `GET /api/v1/services/filter` → Filtra serviços existentes

### Psychologist

* `GET /api/v1/psych/me/availability` → Busca todos os horário cadastrados de serviço
* `POST /api/v1/psych/me/availability` → Adiciona um horário de Trabalho
* `DELETE /api/v1/psych/me/availability` → Deleta um horário de trabalho
* `GET /api/v1/psych/me/appoiments` → Busca o histórico de consultas do psicólogo
* `GET /api/v1/psych/me/next-appoiments` → Busca as proximas consultas confirmadas de um psicólogo
* `GET /api/v1/psych/me/stats/appoiment-count` → Retorna conta de quntas consultas foram criadas no ultimo mês apontado para o psicólogo
* `GET /api/v1/psych/me/stats/rate-appoiments` → Retorna a taxa de confirmação e cancelamento de consultas de um psicólgo
* `GET /api/v1/psych/` → Busca todos os psicólgos ativos cadastrados no sistema
* `POST /api/v1/medical-record` → Cria um prontuário
* `DELETE /api/v1/medical=record` → Deleta um prontuário
* `GET /api/v1/medidcal-record` → Busca todos os prontuários criados
* `GET /api/v1/user/medical-record` → Busca todos os prontuários de um usuário específico

### Appoiments

* `POST /api/v1/appointments` → Realiza o agendamento de uma nova consulta.
* `POST /api/v1/appoiments/simulation` → Simula a disponibilidade e retorna os psicólogos livres na data e hora informadas.
* `POST /api/v1/appoiments/rescheduling` → Solicita o reagendamento de uma consulta.
* `POST /api/v1/appoiments/cancel` → Cancela uma consulta existente.

### Payments

* `POST /api/v1/payments` → Gera as informações necessárias para o processamento do pagamento
* `POST /api/v1/payments/webhook` → Recebe eventos de atualização do status do pagamento via webhook

### Groq

* `POST /api/v1/chat-user` → Envia uma mensagem para processamento e resposta do agente de IA.

---

##  Como Executar

### Pré-requisitos

* Python >=3.14,<4.0 
* Docker
* Docker Compose

###  Configuração

Crie suas variáveis de ambiente:
* Crie um arquivo `.env` na raiz do projeto

```env
DATABASE_URL=sua_url_do_banco
SECRET_KEY=sua_chave
ACESSES_TOKEN_EXPIRE_MINUTES=minutos(ex: 60)
ALGORITHM=HS256
REDIS_URL=sua_url_do_redis
API_KEY_MERCADO_PAGO=sua_chave_do_mercadopago
ENV=prodution( Prodution para testar com o frontend, para realizar os testes deixe como "Test")
API_KEY_GROQ=sua_cheva_do_groq
LINK_FRONTEND=link_do_frontend_rodando_na_sua_maquina
```

Após realizar as configurações realize os proximos passos:

1. Clone o repositório:
```bash
  git clone https://github.com/vitorhugo8899o-lgtm/Psychological-scheduling
```

2. Acesse a pasta do projeto:

```bash
cd Psychological-scheduling
```

3. Suba os containers:

```bash
docker compose up --build
```

4. Instalar as depencias e rodar a aplicação:
```bash
  Poetry:
    poetry install
    poetry shell
    poetry run uvicorn app.main:app --reload

  Ambiente Virtual Padrão (venv):
    # No Linux/macOS:
      python -m venv venv && source venv/bin/activate

    # No Windows:
      python -m venv venv && .\venv\Scripts\activate

      pip install -r requirements.txt  # ou as dependências equivalentes
      uvicorn app.main:app --reload
```
