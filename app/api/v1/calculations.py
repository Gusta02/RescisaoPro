from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.schemas.calculation import CalculationRequest, CalculationResponse, CalculationDetail
from app.schemas.rescisao import RescisaoSaveRequest, RescisaoResponse
from app.services.calculator import RescisaoService
from app.core.database import get_db
from app.models.core import Contrato, Rescisao, ItemRescisao, Usuario
from fastapi.responses import StreamingResponse
from app.services.pdf_service import PDFService
from typing import List

router = APIRouter()

@router.get("/", response_model=List[RescisaoResponse])
async def list_rescisoes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Lista apenas rescisões de contratos que pertencem à imobiliária do usuário
    return db.query(Rescisao).join(Contrato).filter(
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).order_by(Rescisao.id.desc()).all()

@router.post("/simulate", response_model=CalculationResponse)
async def simulate_rescisao(payload: CalculationRequest):
    try:
        # 1. Cálculo de Aluguel Proporcional
        dias, total_mes = RescisaoService.calcular_dias_proporcionais(payload.data_desocupacao)
        valor_aluguel_prop = RescisaoService.calcular_aluguel_proporcional(
            payload.valor_aluguel, payload.data_desocupacao, payload.modo_comercial
        )
        
        # 2. Cálculo da Multa Rescisória
        valor_multa = RescisaoService.calcular_multa_proporcional(
            payload.valor_aluguel,
            payload.data_inicio_contrato,
            payload.data_desocupacao,
            payload.prazo_contrato_meses,
            payload.multa_total_meses
        )

        # 3. NOVO: Cálculo de Encargos Proporcionais (IPTU e Condomínio)
        # Usando o novo método do serviço que criamos na Sprint 8
        valor_iptu_prop = RescisaoService.calcular_encargo_proporcional(
            payload.valor_iptu, payload.data_desocupacao, payload.modo_comercial
        )
        valor_condo_prop = RescisaoService.calcular_encargo_proporcional(
            payload.valor_condominio, payload.data_desocupacao, payload.modo_comercial
        )

        # 4. Montagem dos itens detalhados para o Frontend
        itens = [
            CalculationDetail(
                item="Aluguel Proporcional",
                valor_original=payload.valor_aluguel,
                valor_proporcional=valor_aluguel_prop,
                memoria_calculo=f"{dias}/{total_mes} dias utilizados no mês de saída."
            ),
            CalculationDetail(
                item="Multa Rescisória",
                valor_original=payload.valor_aluguel * payload.multa_total_meses,
                valor_proporcional=valor_multa,
                memoria_calculo=f"Proporcional aos meses restantes do contrato."
            ),
            CalculationDetail(
                item="IPTU Proporcional",
                valor_original=payload.valor_iptu,
                valor_proporcional=valor_iptu_prop,
                memoria_calculo=f"Baseado em {dias} dias de ocupação."
            ),
            CalculationDetail(
                item="Condomínio Proporcional",
                valor_original=payload.valor_condominio,
                valor_proporcional=valor_condo_prop,
                memoria_calculo=f"Baseado em {dias} dias de ocupação."
            )
        ]

        total = valor_aluguel_prop + valor_multa + valor_iptu_prop + valor_condo_prop

        return CalculationResponse(
            data_rescisao=payload.data_desocupacao,
            dias_utilizados=dias,
            itens=itens,
            total_rescisao=total
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
async def save_rescisao(
    payload: RescisaoSaveRequest, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificação de segurança: O contrato alvo pertence a esta imobiliária?
    contrato = db.query(Contrato).filter(
        Contrato.id == payload.contrato_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not contrato:
        raise HTTPException(status_code=403, detail="Contrato não pertence a esta imobiliária")

    try:
        nova_rescisao = Rescisao(
            contrato_id=payload.contrato_id,
            data_desocupacao=payload.data_desocupacao,
            status="FINALIZADO"
        )
        db.add(nova_rescisao)
        db.flush() 

        # Unifica itens calculados (automáticos) e extras (manuais do front)
        todos_itens = payload.itens_calculados + payload.itens_extras
        
        for item in todos_itens:
            db.add(ItemRescisao(
                rescisao_id=nova_rescisao.id,
                descricao=item.descricao,
                tipo=item.tipo, 
                valor=item.valor
            ))
        
        db.commit()
        return {"message": "Rescisão gravada com sucesso!", "rescisao_id": str(nova_rescisao.id)}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {str(e)}")

@router.get("/{rescisao_id}/pdf")
async def download_rescisao_pdf(
    rescisao_id: str, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validação via Join:
    rescisao = db.query(Rescisao).join(Contrato).filter(
        Rescisao.id == rescisao_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not rescisao:
        raise HTTPException(status_code=403, detail="Acesso negado a esta rescisão")

    pdf_buffer = PDFService.gerar_pdf_rescisao(db, rescisao_id)
    filename = f"Termo_Rescisao_{rescisao_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{rescisao_id}/items")
async def get_rescisao_items(
    rescisao_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verifica posse via contrato antes de listar itens
    rescisao = db.query(Rescisao).join(Contrato).filter(
        Rescisao.id == rescisao_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not rescisao:
        raise HTTPException(status_code=404, detail="Rescisão não encontrada")

    return rescisao.itens