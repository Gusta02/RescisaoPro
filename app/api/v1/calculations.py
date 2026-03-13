from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.calculation import CalculationRequest, CalculationResponse, CalculationDetail
from app.schemas.rescisao import RescisaoSaveRequest # Certifique-se de criar este schema
from app.services.calculator import RescisaoService
from app.core.database import get_db
from app.models.core import Rescisao, ItemRescisao
from decimal import Decimal

router = APIRouter()

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

        # 3. Montagem dos itens detalhados
        itens = [
            CalculationDetail(
                item="Aluguel Proporcional",
                valor_original=payload.valor_aluguel,
                valor_proporcional=valor_aluguel_prop,
                memoria_calculo=f"{dias}/{total_mes} dias utilizados."
            ),
            CalculationDetail(
                item="Multa Rescisória",
                valor_original=payload.valor_aluguel * payload.multa_total_meses,
                valor_proporcional=valor_multa,
                memoria_calculo=f"Proporcional aos meses restantes do contrato de {payload.prazo_contrato_meses} meses."
            )
        ]

        total = valor_aluguel_prop + valor_multa

        return CalculationResponse(
            data_rescisao=payload.data_desocupacao,
            dias_utilizados=dias,
            itens=itens,
            total_rescisao=total
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
async def save_rescisao(payload: RescisaoSaveRequest, db: Session = Depends(get_db)):
    try:
        # 1. Criar o registro mestre da Rescisão
        nova_rescisao = Rescisao(
            contrato_id=payload.contrato_id,
            data_desocupacao=payload.data_desocupacao,
            status="FINALIZADO"
        )
        db.add(nova_rescisao)
        db.flush() # Gera o ID da rescisão no banco para usar nos itens abaixo

        # 2. Unificar os itens calculados e os extras
        # Nota: O front-end (Lovable) enviará ambos na lista
        todos_itens = payload.itens_calculados + payload.itens_extras
        
        for item in todos_itens:
            db_item = ItemRescisao(
                rescisao_id=nova_rescisao.id,
                descricao=item.descricao,
                tipo=item.tipo, # "DEBITO" ou "CREDITO"
                valor=item.valor
            )
            db.add(db_item)
        
        db.commit()
        return {"message": "Rescisão gravada com sucesso!", "rescisao_id": str(nova_rescisao.id)}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {str(e)}")