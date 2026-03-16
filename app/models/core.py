from sqlalchemy import Column, String, Numeric, Date, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Imobiliaria(Base):
    __tablename__ = "imobiliarias"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_fantasia = Column(String, nullable=False)
    cnpj = Column(String, unique=True, index=True)
    config_calculo = Column(String, default="MES_CIVIL")

    contratos = relationship("Contrato", back_populates="imobiliaria")

class Contrato(Base):
    __tablename__ = "contratos"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    imobiliaria_id = Column(UUID(as_uuid=True), ForeignKey("imobiliarias.id"))
    locatario_nome = Column(String, nullable=False)
    valor_aluguel = Column(Numeric(10, 2), nullable=False)
    valor_iptu = Column(Numeric(10, 2), default=0.0)
    valor_condominio = Column(Numeric(10, 2), default=0.0)
    data_inicio = Column(Date, nullable=False)
    prazo_meses = Column(Integer, default=30)
    multa_total_meses = Column(Integer, default=3)

    imobiliaria = relationship("Imobiliaria", back_populates="contratos")
    rescisoes = relationship("Rescisao", back_populates="contrato")

class Rescisao(Base):
    __tablename__ = "rescisoes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contrato_id = Column(UUID(as_uuid=True), ForeignKey("contratos.id"))
    data_desocupacao = Column(Date, nullable=False)
    status = Column(String, default="RASCUNHO")

    contrato = relationship("Contrato", back_populates="rescisoes")
    itens = relationship("ItemRescisao", back_populates="rescisao")

class ItemRescisao(Base):
    __tablename__ = "itens_rescisao"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rescisao_id = Column(UUID(as_uuid=True), ForeignKey("rescisoes.id"))
    descricao = Column(String, nullable=False)
    tipo = Column(String, nullable=False) # DEBITO ou CREDITO
    valor = Column(Numeric(10, 2), nullable=False)
    
    rescisao = relationship("Rescisao", back_populates="itens")

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    imobiliaria_id = Column(UUID(as_uuid=True), ForeignKey("imobiliarias.id"))
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    nome = Column(String)

    imobiliaria = relationship("Imobiliaria")