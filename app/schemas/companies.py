from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

# Schema base com campos comuns
class CompanyBase(BaseModel):
    nome_fantasia: str
    cnpj: str
    config_calculo: str = "MES_CIVIL"
    endereco_completo: Optional[str] = None
    telefone_contato: Optional[str] = None
    chave_pix: Optional[str] = None

# Schema para CRIAÇÃO (via Signup ou Admin)
class CompanyCreate(CompanyBase):
    pass

# Schema para ATUALIZAÇÃO (PATCH) - Todos os campos são opcionais aqui
class CompanyUpdate(BaseModel):
    nome_fantasia: Optional[str] = None
    config_calculo: Optional[str] = None
    endereco_completo: Optional[str] = None
    telefone_contato: Optional[str] = None
    chave_pix: Optional[str] = None

# Schema para RESPOSTA (O que a API devolve)
class CompanyResponse(CompanyBase):
    id: UUID
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)