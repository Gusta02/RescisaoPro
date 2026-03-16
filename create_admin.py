from app.core.database import SessionLocal
from app.models.core import Usuario, Imobiliaria
from app.core.security import gerar_hash_senha
import uuid

def create_first_user():
    db = SessionLocal()
    try:
        # 1. Busca a primeira imobiliária cadastrada
        imobiliaria = db.query(Imobiliaria).first()
        if not imobiliaria:
            print("❌ Erro: Nenhuma imobiliária encontrada. Cadastre uma primeiro pelo Swagger.")
            return

        # 2. Dados do seu usuário
        email = "gustavo@recisaopro.com.br" # Seu e-mail de acesso
        senha = "admin123"                # Sua senha (mude depois!)
        
        # 3. Verifica se o usuário já existe
        user_exists = db.query(Usuario).filter(Usuario.email == email).first()
        if user_exists:
            print(f"⚠️ Usuário {email} já cadastrado.")
            return

        # 4. Cria o usuário com a senha hasheada
        novo_usuario = Usuario(
            email=email,
            nome="Gustavo Admin",
            senha_hash=gerar_hash_senha(senha),
            imobiliaria_id=imobiliaria.id
        )

        db.add(novo_usuario)
        db.commit()
        print(f"✅ Usuário criado com sucesso!")
        print(f"📧 E-mail: {email}")
        print(f"🔑 Senha: {senha}")
        print(f"🏢 Vinculado à: {imobiliaria.nome_fantasia}")

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_first_user()