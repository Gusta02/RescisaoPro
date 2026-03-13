from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.core import Contrato
from app.schemas.rescisao import ContratoCreate # Use aquele schema que definimos
from typing import List

router = APIRouter()

@router.post("/")
async def create_contract(imobiliaria_id: str, payload: ContratoCreate, db: Session = Depends(get_db)):
    db_item = Contrato(**payload.dict(), imobiliaria_id=imobiliaria_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[dict]) # Endpoint simples para listar IDs
async def list_contracts(db: Session = Depends(get_db)):
    return db.query(Contrato).all()