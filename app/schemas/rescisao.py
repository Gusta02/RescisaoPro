#app/schemas/rescisao.py
import uuid
from pydantic import BaseModel, ConfigDict, model_validator, Field
from datetime import date
from decimal import Decimal
from uuid import UUID
from typing import List, Optional



# --- SCHEMAS DE CONTRATO ---
class ContratoCreate(BaseModel):
    locatario_nome: str
    valor_aluguel: float
    valor_iptu: Optional[float] = 0.0
    valor_condominio: Optional[float] = 0.0
    data_inicio: date
    prazo_meses: int
    multa_total_meses: int

class ContratoResponse(BaseModel):
    id: UUID
    locatario_nome: str
    valor_aluguel: Decimal
    data_inicio: date
    imobiliaria_id: UUID

    model_config = ConfigDict(from_attributes=True)

# --- SCHEMAS DE RESCISÃO ---

class ItemAdicional(BaseModel):
    descricao: str
    tipo: str  # "DEBITO" ou "CREDITO"
    valor: Decimal

class RescisaoRequest(BaseModel):
    contrato_id: UUID
    data_desocupacao: date

class RescisaoSaveRequest(BaseModel):
    contrato_id: UUID
    data_desocupacao: date
    itens_calculados: List[ItemAdicional]
    itens_extras: List[ItemAdicional]
    
    # --- NOVOS CAMPOS SPRINT 11 ---
    status: Optional[str] = "RASCUNHO"
    motivo_saida: Optional[str] = None
    observacoes: Optional[str] = None
    
    # Checklist Operacional
    chaves_devolvidas: bool = False
    contas_consumo_quitadas: bool = False
    controle_portao_devolvido: bool = False
    vistorias_concluidas: bool = False

class RescisaoWorkflowUpdate(BaseModel):
    """Schema específico para atualizar o progresso da rescisão"""
    status: Optional[str] = None
    motivo_saida: Optional[str] = None
    chaves_devolvidas: Optional[bool] = None
    contas_consumo_quitadas: Optional[bool] = None
    controle_portao_devolvido: Optional[bool] = None
    vistorias_concluidas: Optional[bool] = None
    observacoes: Optional[str] = None

class RescisaoResponse(BaseModel):
    id: UUID
    contrato_id: UUID
    data_desocupacao: date
    status: str
    
    # Use o Field do Pydantic V2 (sem o .v1)
    observacoes: Optional[str] = Field(None, alias="observacoes_internas")
    motivo_saida: Optional[str] = None
    
    chaves_devolvidas: bool = False
    contas_consumo_quitadas: bool = False
    controle_portao_devolvido: bool = False
    vistorias_concluidas: bool = False
    locatario_nome: Optional[str] = "Não informado"

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @model_validator(mode='before')
    @classmethod
    def pre_fill_data(cls, data):
        if not isinstance(data, dict):
            # Injeta locatario_nome
            contrato = getattr(data, "contrato", None)
            if contrato:
                setattr(data, "locatario_nome", getattr(contrato, "locatario_nome", "Não informado"))
            
            # Limpa nulos dos booleanos
            for field in ["chaves_devolvidas", "contas_consumo_quitadas", "controle_portao_devolvido", "vistorias_concluidas"]:
                if getattr(data, field, None) is None:
                    setattr(data, field, False)
        return data
    
 
class ReparoCreate(BaseModel):
    item_ambiente: str
    descricao_dano: Optional[str] = None
    valor_orcado: float
    responsabilidade: str = "LOCATARIO"

class ReparoResponse(BaseModel):
    id: UUID
    item_ambiente: str
    descricao_dano: Optional[str]
    valor_orcado: Decimal
    responsabilidade: str
    status_reparo: str

    model_config = ConfigDict(from_attributes=True)