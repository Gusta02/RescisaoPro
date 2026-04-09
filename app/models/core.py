# app/models/core.py
from typing import Optional

from pydantic import Field
from sqlalchemy import Boolean, Column, String, Numeric, Date, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Imobiliaria(Base):
    __tablename__ = "imobiliarias"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_fantasia = Column(String, nullable=False)
    cnpj = Column(String, unique=True, index=True, nullable=False)
    config_calculo = Column(String, default="MES_CIVIL")
    
    # --- NOVOS CAMPOS SPRINT 10 ---
    logo_url = Column(String, nullable=True)
    endereco_completo = Column(String, nullable=True)
    telefone_contato = Column(String, nullable=True)
    chave_pix = Column(String, nullable=True)

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
    
    status = Column(String, default="RASCUNHO") # RASCUNHO, AGUARDANDO_APROVACAO, FINALIZADO
    motivo_saida = Column(String, nullable=True) # Ex: VALOR_ALUGUEL, COMPRA_IMOVEL, MANUTENCAO
    observacoes_internas = Column(Text, nullable=True)
    chaves_devolvidas = Column(Boolean, default=False)
    contas_consumo_quitadas = Column(Boolean, default=False)
    controle_portao_devolvido = Column(Boolean, default=False)
    vistorias_concluidas = Column(Boolean, default=False)


    contrato = relationship("Contrato", back_populates="rescisoes")
    itens = relationship("ItemRescisao", back_populates="rescisao")
    # Dentro da classe Rescisao
    criado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    # Relacionamento para facilitar a busca do nome do funcionário
    autor = relationship("Usuario", foreign_keys=[criado_por])
    reparos = relationship("ReparoRescisao", back_populates="rescisao", cascade="all, delete-orphan")

class ReparoRescisao(Base):
    __tablename__ = "reparos_rescisao"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rescisao_id = Column(UUID(as_uuid=True), ForeignKey("rescisoes.id"))
    
    item_ambiente = Column(String, nullable=False) # Ex: "Sala - Pintura", "Cozinha - Torneira"
    descricao_dano = Column(Text, nullable=True)
    valor_orcado = Column(Numeric(10, 2), default=0.0)
    
    # Define quem deve pagar: LOCATARIO ou PROPRIETARIO (ou A_DEFINIR)
    responsabilidade = Column(String, default="LOCATARIO")
    
    # Status do conserto
    status_reparo = Column(String, default="PENDENTE") # PENDENTE, EM_EXECUCAO, CONCLUIDO
    
    rescisao = relationship("Rescisao", back_populates="reparos")

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