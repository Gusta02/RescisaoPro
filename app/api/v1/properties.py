from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.core import Contrato
from app.schemas.rescisao import ContratoCreate, ContratoResponse  
from app.services.pdf_service import PDFService
from app.api.v1.deps import get_current_user
from app.models.core import Usuario

router = APIRouter()

@router.post("/")
async def create_contract(imobiliaria_id: str, payload: ContratoCreate, db: Session = Depends(get_db)):
    db_item = Contrato(**payload.dict(), imobiliaria_id=imobiliaria_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/", response_model=List[ContratoResponse])
async def list_contracts(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user) # Injeta o usuário logado
):
    # FILTRO DE SEGURANÇA: Só busca contratos da imobiliária do usuário
    contracts = db.query(Contrato).filter(Contrato.imobiliaria_id == current_user.imobiliaria_id).all()
    return contracts
    
@router.get("/{contrato_id}/pdf")
async def download_contrato_pdf(contrato_id: str, db: Session = Depends(get_db)):
    pdf_buffer = PDFService.gerar_pdf_contrato(db, contrato_id)
    filename = f"Contrato_{contrato_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )