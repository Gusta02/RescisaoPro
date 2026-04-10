from pydantic import BaseModel, EmailStr

class UserCompanyCreate(BaseModel):
    # Dados da Imobiliária
    nome_fantasia: str
    cnpj: str
    
    # Dados do Primeiro Usuário (Admin)
    nome: str
    email: EmailStr
    senha: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    token: str
    nova_senha: str