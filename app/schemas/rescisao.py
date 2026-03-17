import uuid

from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import List, Optional

class ContratoCreate(BaseModel):
    locatario_nome: str
    valor_aluguel: float
    valor_iptu: Optional[float] = 0.0
    valor_condominio: Optional[float] = 0.0
    data_inicio: date
    prazo_meses: int
    multa_total_meses: int

class RescisaoRequest(BaseModel):
    contrato_id: UUID
    data_desocupacao: date

class ItemAdicional(BaseModel):
    descricao: str
    tipo: str  # "DEBITO" ou "CREDITO"
    valor: Decimal

class RescisaoSaveRequest(BaseModel):
    contrato_id: UUID
    data_desocupacao: date
    itens_calculados: List[ItemAdicional] # Aluguel, Multa, etc.
    itens_extras: List[ItemAdicional]     # Pintura, Reparos, etc.
    observacoes: Optional[str] = None

class ContratoResponse(BaseModel):
    id: UUID
    locatario_nome: str
    valor_aluguel: Decimal
    data_inicio: date
    imobiliaria_id: UUID

    class Config:
        from_attributes = True

class RescisaoResponse(BaseModel):
    id: uuid.UUID
    contrato_id: uuid.UUID
    data_desocupacao: date
    status: str
    # Opcional: incluir o nome do locatário via relação
    locatario_nome: Optional[str] = None 

    class Config:
        from_attributes = True