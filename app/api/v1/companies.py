from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.core import Imobiliaria
from pydantic import BaseModel
import uuid

router = APIRouter()

class ImobiliariaCreate(BaseModel):
    nome_fantasia: str
    cnpj: str

@router.post("/")
async def create_company(payload: ImobiliariaCreate, db: Session = Depends(get_db)):
    db_item = Imobiliaria(nome_fantasia=payload.nome_fantasia, cnpj=payload.cnpj)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item