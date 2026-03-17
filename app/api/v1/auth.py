from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.security import verificar_senha, criar_token_acesso
from app.models.core import Usuario

router = APIRouter()

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