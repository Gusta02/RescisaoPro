from pydantic import BaseModel
from datetime import date
from typing import List, Optional, Dict, Any
from enum import Enum

class EventType(str, Enum):
    REAJUSTE = "REAJUSTE"
    VENCIMENTO = "VENCIMENTO"
    DESOCUPACAO = "DESOCUPACAO"

class Priority(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"

class ManagementEvent(BaseModel):
    data: date
    tipo: EventType
    titulo: str
    descricao: str
    prioridade: Priority
    metadata: Dict[str, Any] # Para passar IDs de contrato ou rescisão

class DashboardSummary(BaseModel):
    total_eventos: int
    eventos: List[ManagementEvent]