from fastapi import FastAPI
from app.core.database import engine, Base
from app.api.v1 import calculations, companies, properties, auth, deps


# Nota: Como você está usando Alembic, o create_all é opcional, 
# mas no MVP ajuda a garantir que as tabelas existam.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RescisaoPro API")

# Inclua o router de cálculos com o prefixo correto
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticação"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Imobiliarias"])
app.include_router(properties.router, prefix="/api/v1/contracts", tags=["Contratos"])
app.include_router(calculations.router, prefix="/api/v1/calculations", tags=["Calculos"])

@app.get("/")
async def root():
    return {"message": "RescisaoPro API is running"}