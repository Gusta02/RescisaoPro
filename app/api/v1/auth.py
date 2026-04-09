from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.security import verificar_senha, criar_token_acesso, get_password_hash
from app.models.core import Usuario, Imobiliaria
from app.schemas.auth import UserCompanyCreate

router = APIRouter()

@router.post("/signup")
async def signup_new_company(payload: UserCompanyCreate, db: Session = Depends(get_db)):
    # 1. Verificar se CNPJ ou E-mail já existem para evitar erros duplicados
    existing_cnpj = db.query(Imobiliaria).filter(Imobiliaria.cnpj == payload.cnpj).first()
    if existing_cnpj:
        raise HTTPException(status_code=400, detail="Este CNPJ já está cadastrado.")
        
    existing_user = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Este e-mail já está em uso.")

    try:
        # 2. Criar a Imobiliária Primeiro
        nova_empresa = Imobiliaria(
            nome_fantasia=payload.nome_fantasia,
            cnpj=payload.cnpj
        )
        db.add(nova_empresa)
        db.flush() # Gera o ID da empresa sem comitar a transação ainda

        # 3. Criar o Usuário vinculado à empresa recém-criada
        novo_admin = Usuario(
            nome=payload.nome,
            email=payload.email,
            senha_hash=get_password_hash(payload.senha),
            imobiliaria_id=nova_empresa.id # O vínculo acontece aqui!
        )
        db.add(novo_admin)
        
        # 4. Comita ambos de uma vez só
        db.commit()
        
        return {"message": "Conta SaaS criada com sucesso! Agora você pode fazer login."}

    except Exception as e:
        db.rollback() # Se algo der errado (ex: erro de banco), desfaz tudo
        raise HTTPException(status_code=500, detail=f"Erro no cadastro: {str(e)}")

@router.post("/login")
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    if not user or not verificar_senha(form_data.password, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = criar_token_acesso(data={"sub": user.email, "imobiliaria_id": str(user.imobiliaria_id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "nome": current_user.nome,
        "email": current_user.email,
        "imobiliaria_id": str(current_user.imobiliaria_id)
    }