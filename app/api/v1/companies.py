from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.core import Imobiliaria, Usuario
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

@router.get("/me")
async def get_my_company(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    company = db.query(Imobiliaria).filter(Imobiliaria.id == current_user.imobiliaria_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Imobiliária não encontrada")
    return company

@router.patch("/me")
async def update_my_company(
    payload: ImobiliariaCreate, # Reaproveitando o schema ou criando um parcial
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    company = db.query(Imobiliaria).filter(Imobiliaria.id == current_user.imobiliaria_id).first()
    
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(company, key, value)
    
    db.commit()
    return company