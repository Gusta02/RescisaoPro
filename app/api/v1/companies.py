from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.core import Imobiliaria, Usuario
from app.schemas.companies import CompanyUpdate, CompanyResponse
from pydantic import BaseModel
import uuid
import shutil
import os

UPLOAD_DIR = "uploads/logos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

@router.patch("/me", response_model=CompanyResponse)
async def update_my_company(
    payload: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Busca a imobiliária do usuário logado
    imobiliaria = db.query(Imobiliaria).filter(
        Imobiliaria.id == current_user.imobiliaria_id
    ).first()
    
    if not imobiliaria:
        raise HTTPException(status_code=404, detail="Imobiliária não encontrada")

    # Converte o payload em dicionário, ignorando campos não enviados (exclude_unset)
    update_data = payload.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(imobiliaria, key, value)

    try:
        db.commit()
        db.refresh(imobiliaria)
        return imobiliaria
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")

@router.post("/me/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Validar extensão (apenas imagens)
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="O arquivo deve ser uma imagem.")

    # 2. Criar nome único para o arquivo (usando o ID da imobiliária)
    file_extension = file.filename.split(".")[-1]
    file_path = f"{UPLOAD_DIR}/{current_user.imobiliaria_id}.{file_extension}"

    # 3. Salvar o arquivo fisicamente
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 4. Atualizar o banco de dados
    imobiliaria = db.query(Imobiliaria).filter(Imobiliaria.id == current_user.imobiliaria_id).first()
    imobiliaria.logo_url = file_path
    db.commit()

    return {"message": "Logo atualizado com sucesso!", "path": file_path}