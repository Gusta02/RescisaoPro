# app/api/v1/calculations.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.v1.deps import get_current_user
from app.schemas.calculation import CalculationRequest, CalculationResponse, CalculationDetail
from app.schemas.rescisao import ReparoResponse, RescisaoSaveRequest, RescisaoResponse, RescisaoWorkflowUpdate, ReparoCreate
from app.services.calculator import RescisaoService
from app.core.database import get_db
from app.models.core import Contrato, ReparoRescisao, Rescisao, ItemRescisao, Usuario
from fastapi.responses import StreamingResponse
from app.services.pdf_service import PDFService
from typing import List
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[RescisaoResponse])
async def list_rescisoes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Rescisao).options(joinedload(Rescisao.contrato)).join(Contrato).filter(
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).order_by(Rescisao.id.desc()).all()

@router.delete("/{rescisao_id}/reparos/{reparo_id}")
async def delete_reparo(
    rescisao_id: UUID,
    reparo_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Verifica se o reparo pertence a uma rescisão da imobiliária
    reparo = db.query(ReparoRescisao).join(Rescisao).join(Contrato).filter(
        ReparoRescisao.id == reparo_id,
        Rescisao.id == rescisao_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not reparo:
        raise HTTPException(status_code=404, detail="Reparo não encontrado")

    # 2. Busca e remove o item financeiro automático gerado por este reparo
    # Dica: Buscamos pelo nome exato que usamos no POST: "Reparo: {item_ambiente}"
    descricao_busca = f"Reparo: {reparo.item_ambiente}"
    item_financeiro = db.query(ItemRescisao).filter(
        ItemRescisao.rescisao_id == rescisao_id,
        ItemRescisao.descricao == descricao_busca
    ).first()

    if item_financeiro:
        db.delete(item_financeiro)

    # 3. Deleta o reparo
    db.delete(reparo)
    db.commit()

    return {"message": "Reparo e débito financeiro removidos com sucesso"}


@router.post("/simulate", response_model=CalculationResponse)
async def simulate_rescisao(payload: CalculationRequest):
    try:
        # 1. Cálculo de Aluguel Proporcional
        dias, total_mes = RescisaoService.calcular_dias_proporcionais(payload.data_desocupacao)
        valor_aluguel_prop = RescisaoService.calcular_aluguel_proporcional(
            payload.valor_aluguel, payload.data_desocupacao, payload.modo_comercial
        )
        
        # 2. Cálculo da Multa Rescisória (Com suporte a isenção da Sprint 9)
        valor_multa = RescisaoService.calcular_multa_proporcional(
            payload.valor_aluguel,
            payload.data_inicio_contrato,
            payload.data_desocupacao,
            payload.prazo_contrato_meses,
            payload.multa_total_meses,
            payload.isentar_multa # Nova flag
        )

        # 3. Cálculo de Encargos Proporcionais (IPTU e Condomínio)
        valor_iptu_prop = RescisaoService.calcular_encargo_proporcional(
            payload.valor_iptu, payload.data_desocupacao, payload.modo_comercial
        )
        valor_condo_prop = RescisaoService.calcular_encargo_proporcional(
            payload.valor_condominio, payload.data_desocupacao, payload.modo_comercial
        )

        # --- NORMALIZAÇÃO DE TIPOS (Evita erro Decimal + Float) ---
        v_aluguel_f = float(valor_aluguel_prop)
        v_multa_f = float(valor_multa)
        v_iptu_f = float(valor_iptu_prop)
        v_condo_f = float(valor_condo_prop)

        # 4. Definição da Memória de Cálculo da Multa (Dinâmica)
        msg_multa = "Isenção de multa aplicada conforme negociação." if payload.isentar_multa \
                    else "Proporcional aos meses restantes do contrato."

        # 5. Montagem dos itens detalhados para o Frontend
        itens = [
            CalculationDetail(
                item="Aluguel Proporcional",
                valor_original=float(payload.valor_aluguel),
                valor_proporcional=v_aluguel_f,
                memoria_calculo=f"{dias}/{total_mes} dias utilizados no mês de saída."
            ),
            CalculationDetail(
                item="Multa Rescisória",
                valor_original=float(payload.valor_aluguel * payload.multa_total_meses),
                valor_proporcional=v_multa_f,
                memoria_calculo=msg_multa
            ),
            CalculationDetail(
                item="IPTU Proporcional",
                valor_original=float(payload.valor_iptu),
                valor_proporcional=v_iptu_f,
                memoria_calculo=f"Baseado em {dias} dias de ocupação no mês."
            ),
            CalculationDetail(
                item="Condomínio Proporcional",
                valor_original=float(payload.valor_condominio),
                valor_proporcional=v_condo_f,
                memoria_calculo=f"Baseado em {dias} dias de ocupação no mês."
            )
        ]

        # 6. Soma do Total Final (Segura contra erros de tipo)
        total_rescisao = v_aluguel_f + v_multa_f + v_iptu_f + v_condo_f

        return CalculationResponse(
            data_rescisao=payload.data_desocupacao,
            dias_utilizados=dias,
            itens=itens,
            total_rescisao=round(total_rescisao, 2)
        )
    

    except Exception as e:
        # Log para facilitar sua depuração no terminal
        print(f"Erro na simulação: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
async def save_rescisao(
    payload: RescisaoSaveRequest, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Verificação de segurança: Multi-tenant
    contrato = db.query(Contrato).filter(
        Contrato.id == payload.contrato_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not contrato:
        raise HTTPException(status_code=403, detail="Contrato não pertence a esta imobiliária")

    # 2. Trava de Duplicidade 
    # Agora verificamos se já existe QUALQUER rescisão para não poluir o banco, 
    # ou permitimos apenas uma FINALIZADA.
    rescisao_existente = db.query(Rescisao).filter(
        Rescisao.contrato_id == payload.contrato_id,
        Rescisao.status == "FINALIZADO"
    ).first()

    if rescisao_existente:
        raise HTTPException(
            status_code=400, 
            detail="Este contrato já possui uma rescisão finalizada no sistema."
        )

    try:
        # 3. Criar o registro mestre com os campos da Sprint 11
        nova_rescisao = Rescisao(
            contrato_id=payload.contrato_id,
            data_desocupacao=payload.data_desocupacao,
            status=payload.status or "RASCUNHO",  # Inicia como rascunho por padrão
            motivo_saida=payload.motivo_saida,
            observacoes_internas=payload.observacoes,
            # Checklist vindo do Payload
            chaves_devolvidas=payload.chaves_devolvidas,
            contas_consumo_quitadas=payload.contas_consumo_quitadas,
            controle_portao_devolvido=payload.controle_portao_devolvido,
            vistorias_concluidas=payload.vistorias_concluidas,
            # Auditoria
            criado_por=current_user.id 
        )
        db.add(nova_rescisao)
        db.flush() 

        # 4. Salvar Itens (Calculados + Extras)
        todos_itens = payload.itens_calculados + payload.itens_extras
        
        for item in todos_itens:
            db.add(ItemRescisao(
                rescisao_id=nova_rescisao.id,
                descricao=item.descricao,
                tipo=item.tipo,
                valor=float(item.valor) 
            ))
        
        db.commit()
        return {
            "status": "success",
            "message": "Rescisão e checklist gravados com sucesso!", 
            "rescisao_id": str(nova_rescisao.id),
            "workflow_status": nova_rescisao.status
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno ao salvar: {str(e)}"
        )
    
@router.patch("/{rescisao_id}/workflow")
async def update_rescisao_workflow(
    rescisao_id: UUID,
    payload: RescisaoWorkflowUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Busca a rescisão garantindo que pertence à imobiliária do usuário logado (Join com Contrato)
    rescisao = db.query(Rescisao).join(Contrato).filter(
        Rescisao.id == rescisao_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()

    if not rescisao:
        raise HTTPException(status_code=404, detail="Rescisão não encontrada ou acesso negado")

    # Atualiza apenas os campos enviados no JSON (ignore o que for None)
    update_data = payload.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(rescisao, key, value)

    # Regra de Negócio: Se tentar FINALIZAR, podemos validar se o checklist está ok
    if rescisao.status == "FINALIZADO":
        if not all([rescisao.chaves_devolvidas, rescisao.vistorias_concluidas]):
            # Aqui é opcional: você pode apenas avisar ou bloquear
            pass 

    db.commit()
    db.refresh(rescisao)
    
    return {"message": "Status do processo atualizado!", "status": rescisao.status}

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

@router.post("/{rescisao_id}/reparos", response_model=ReparoResponse)
async def add_reparo(
    rescisao_id: UUID,
    payload: ReparoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. Validar posse da rescisão
    rescisao = db.query(Rescisao).join(Contrato).filter(
        Rescisao.id == rescisao_id,
        Contrato.imobiliaria_id == current_user.imobiliaria_id
    ).first()
    
    if not rescisao:
        raise HTTPException(status_code=404, detail="Rescisão não encontrada")

    # 2. Criar o reparo
    novo_reparo = ReparoRescisao(
        rescisao_id=rescisao_id,
        item_ambiente=payload.item_ambiente,
        descricao_dano=payload.descricao_dano,
        valor_orcado=payload.valor_orcado,
        responsabilidade=payload.responsabilidade
    )
    db.add(novo_reparo)
    
    # 3. REGRA DE OURO: Se for responsabilidade do locatário, vira um débito financeiro
    if payload.responsabilidade == "LOCATARIO" and payload.valor_orcado > 0:
        novo_item = ItemRescisao(
            rescisao_id=rescisao_id,
            descricao=f"Reparo: {payload.item_ambiente}",
            tipo="DEBITO",
            valor=payload.valor_orcado
        )
        db.add(novo_item)
        
    db.commit()
    db.refresh(novo_reparo)
    return novo_reparo

@router.get("/{rescisao_id}/reparos", response_model=List[ReparoResponse])
async def list_reparos(
    rescisao_id: UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(ReparoRescisao).filter(ReparoRescisao.rescisao_id == rescisao_id).all()