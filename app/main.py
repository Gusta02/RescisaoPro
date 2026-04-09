from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.v1 import calculations, companies, properties, auth, deps
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# Nota: Como você está usando Alembic, o create_all é opcional, 
# mas no MVP ajuda a garantir que as tabelas existam.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RescisaoPro API")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Porta comum de projetos Vite/React
    "*", # Permite todas as origens (ideal para testes iniciais com Lovable)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"], # Permite todos os headers (incluindo o de Autenticação)
)


# Inclua o router de cálculos com o prefixo correto
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Imobiliarias"])
app.include_router(properties.router, prefix="/api/v1/contracts", tags=["Contratos"])
app.include_router(calculations.router, prefix="/api/v1/calculations", tags=["Calculos"])

@app.get("/")
async def root():
    return {"message": "RescisaoPro API is running"}