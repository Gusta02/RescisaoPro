from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# O engine é o "cano" de conexão
engine = create_engine(settings.DATABASE_URL)

# A SessionLocal é a fábrica de conversas com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os nossos Models herdarem
Base = declarative_base()

# Função que abre e fecha a conexão por requisição
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()