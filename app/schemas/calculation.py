from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

# O que o Front-end envia
class CalculationRequest(BaseModel):
    valor_aluguel: Decimal
    valor_iptu: Decimal = Decimal("0.00")
    valor_condominio: Decimal = Decimal("0.00")
    data_inicio_contrato: date
    data_desocupacao: date
    prazo_contrato_meses: int = 30
    multa_total_meses: int = 3
    modo_comercial: bool = False  
    isentar_multa: bool = False

# O que o Front-end recebe (detalhado para gerar valor percebido)
class CalculationDetail(BaseModel):
    item: str
    valor_original: Decimal
    valor_proporcional: Decimal
    memoria_calculo: str

class CalculationResponse(BaseModel):
    data_rescisao: date
    dias_utilizados: int
    itens: List[CalculationDetail]
    total_rescisao: Decimal