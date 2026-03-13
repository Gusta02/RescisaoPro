from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "Rescisão Pro"
    
    # Adicione as variáveis que estão no seu .env aqui:
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        # Isso ignora se houver mais coisas no .env que não estão aqui
        extra = "ignore" 

settings = Settings()