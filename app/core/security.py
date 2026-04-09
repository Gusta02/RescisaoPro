from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def gerar_hash_senha(senha: str):
    # Forçamos a conversão para garantir que não haja lixo de memória
    if isinstance(senha, str):
        senha = senha.encode('utf-8')
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """Compara a senha digitada com o hash do banco"""
    return pwd_context.verify(senha_plana, senha_hash)

def get_password_hash(senha: str) -> str:
    """Gera o hash seguro para salvar no banco de dados"""
    return pwd_context.hash(senha)

def criar_token_acesso(data: dict):
    para_codificar = data.copy()
    expira = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    para_codificar.update({"exp": expira})
    return jwt.encode(para_codificar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)