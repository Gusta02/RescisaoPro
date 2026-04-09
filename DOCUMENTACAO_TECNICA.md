# Documentação Técnica — RescisaoPro

## 1. Visão Geral
API RESTful com FastAPI para gestão de rescisões de contratos de locação, com suporte a:
- Autenticação JWT (OAuth2 password flow)
- Multi-tenant por imobiliária
- Cálculos de rescisão (aluguel proporcional, multa, IPTU e condomínio)
- Criação e listagem de contratos, rescisões e itens de rescisão
- Geração de PDFs de contrato e termo de rescisão

## 2. Stack
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL (ou outro via DATABASE_URL)
- Alembic (migrations)
- xhtml2pdf + Jinja2 (PDF)
- passlib bcrypt (hash de senha)

## 3. Arquitetura de Código
- `app/main.py` (app + rotas + CORS)
- `app/core/database.py` (engine, SessionLocal, Base, `get_db`)
- `app/core/config.py` (settings + .env)
- `app/core/security.py` (hash + token JWT)
- `app/api/v1/*` (rotas em namespace)
- `app/models/core.py` (SQLAlchemy models)
- `app/schemas` (Pydantic models)
- `app/services` (lógica de negócio e PDF)
- `app/template` (HTML para PDF)

## 4. Modelos / Tabelas
### Imobiliaria
- id (UUID PK)
- nome_fantasia
- cnpj (único)
- config_calculo (default MES_CIVIL)

### Contrato
- id (UUID PK)
- imobiliaria_id (FK)
- locatario_nome
- valor_aluguel
- valor_iptu
- valor_condominio
- data_inicio
- prazo_meses
- multa_total_meses

### Rescisao
- id (UUID PK)
- contrato_id (FK)
- data_desocupacao
- status

### ItemRescisao
- id (UUID PK)
- rescisao_id (FK)
- descricao
- tipo (DEBITO/CREDITO)
- valor

### Usuario
- id (UUID PK)
- imobiliaria_id (FK)
- email (único)
- senha_hash
- nome

## 5. Autenticação
- `POST /api/v1/auth/login` (form URL-encoded)
- `GET /api/v1/auth/me`
- Dependência: `app.api.v1.deps.get_current_user`
- Token contém: sub=email, imobiliaria_id

## 6. Rotas
### /api/v1/companies
`POST /` cria imobiliária
`GET /me` obtém dados da imobiliária do usuário
`PATCH /me` atualiza dados

### /api/v1/contracts
`POST /` cria contrato (associa imobiliária do usuário)
`GET /` lista contratos da imobiliária
`GET /{contrato_id}` mostra contrato
`GET /{contrato_id}/pdf` gera PDF de contrato

### /api/v1/calculations
`GET /` lista rescisões da imobiliária
`POST /simulate` simula cálculo (retorna detalhes)
`POST /save` salva rescisão + itens
`GET /{rescisao_id}/pdf` gera PDF de termo de rescisão
`GET /{rescisao_id}/items` lista itens da rescisão

## 7. Lógica de Cálculo
`app/services/calculator.py` com métodos:
- calcular_dias_proporcionais
- calcular_aluguel_proporcional
- calcular_multa_proporcional
- calcular_encargo_proporcional

## 8. Geração de PDF
`app/services/pdf_service.py`:
- gerar_pdf_rescisao
- gerar_pdf_contrato
Templates:
- `app/template/termo_rescisao.html`
- `app/template/contrato_locacao.html`

## 9. Configurações
- `.env` contém:
  - DATABASE_URL
  - SECRET_KEY
  - ALGORITHM (HS256)
  - ACCESS_TOKEN_EXPIRE_MINUTES

## 10. Observações
- proteção com token e validação de imobiliária nas queries
- exceções com códigos HTTP corretos (401/403/404/500)
- `Base.metadata.create_all(bind=engine)` em `app/main.py`
- a aplicação já expõe Swagger UI em `/docs`
