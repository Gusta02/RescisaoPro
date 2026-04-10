from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.core import Usuario
from app.services.management_service import ManagementService

router = APIRouter()

@router.get("/summary")
async def get_management_summary(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna alertas inteligentes sobre contratos e rescisões 
    específicos para a imobiliária do usuário.
    """
    return ManagementService.get_dashboard_summary(db, current_user.imobiliaria_id)

@router.get("/dashboard")
async def get_full_dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Chama a lógica de alertas e calendário (Sprint 13)
    summary = ManagementService.get_dashboard_summary(db, current_user.imobiliaria_id)
    
    # 2. Chama a lógica de métricas financeiras (Sprint 14) - AQUI ESTÁ A CHAMADA!
    kpis = ManagementService.get_business_kpis(db, current_user.imobiliaria_id)
    
    # 3. Retorna o "Combo" completo para o Dashboard
    return {
        "status": "success",
        "kpis": kpis,
        "alerts": summary
    }