# app/services/pdf_service.py
import os
from io import BytesIO
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from app.models.core import Rescisao, Contrato, ReparoRescisao, Imobiliaria # Adicionado Imobiliaria
from fastapi import HTTPException

class PDFService:
    @staticmethod
    def _get_template_env():
        """Helper para carregar o ambiente Jinja2"""
        template_path = os.path.join(os.path.dirname(__file__), "..", "template")
        return Environment(loader=FileSystemLoader(template_path))

    @staticmethod
    def _format_currency(valor: float) -> str:
        """Helper para formatar moeda no padrão BR"""
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def gerar_pdf_rescisao(db: Session, rescisao_id: str):
        # 1. Busca os dados com as relações
        rescisao = db.query(Rescisao).filter(Rescisao.id == rescisao_id).first()
        if not rescisao:
            raise HTTPException(status_code=404, detail="Rescisão não encontrada")
        
        contrato = rescisao.contrato
        imobiliaria = contrato.imobiliaria

        # --- NOVO: Busca de Reparos (Sprint 12) ---
        reparos = db.query(ReparoRescisao).filter(ReparoRescisao.rescisao_id == rescisao_id).all()
        total_reparos = sum(float(r.valor_orcado) for r in reparos if r.responsabilidade == "LOCATARIO")

        # --- Branding: Caminho Absoluto do Logo ---
        if imobiliaria.logo_url:
            caminho_relativo = imobiliaria.logo_url.lstrip('/')
            imobiliaria.logo_abspath = os.path.abspath(os.path.join(os.getcwd(), caminho_relativo))
        else:
            imobiliaria.logo_abspath = None

        # 2. Cálculos Financeiros
        total_debito = sum(item.valor for item in rescisao.itens if item.tipo == "DEBITO")
        total_credito = sum(item.valor for item in rescisao.itens if item.tipo == "CREDITO")
        total_final = float(total_debito) - float(total_credito)

        # 3. Dados para o Template
        dados_template = {
            "imobiliaria": imobiliaria,
            "locatario_nome": contrato.locatario_nome,
            "data_desocupacao": rescisao.data_desocupacao.strftime("%d/%m/%Y"),
            "itens": rescisao.itens,
            "reparos": reparos, # <--- Injetado
            "total_reparos": PDFService._format_currency(total_reparos),
            "total_final": PDFService._format_currency(total_final),
            "total_debito": PDFService._format_currency(total_debito),
            "total_credito": PDFService._format_currency(total_credito)
        }

        # 4. Renderização e Conversão
        env = PDFService._get_template_env()
        template = env.get_template("termo_rescisao.html")
        html_content = template.render(dados_template)

        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            raise HTTPException(status_code=500, detail="Erro ao gerar PDF")

        pdf_buffer.seek(0)
        return pdf_buffer
    
    @staticmethod
    def gerar_pdf_contrato(db: Session, contrato_id: str):
        contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
        if not contrato:
            raise HTTPException(status_code=404, detail="Contrato não encontrado")

        imobiliaria = contrato.imobiliaria

        if imobiliaria.logo_url:
            # Remove a barra inicial se houver (ex: /uploads/logo.png -> uploads/logo.png)
            caminho_relativo = imobiliaria.logo_url.lstrip('/')
            
            # Cria o caminho completo no seu computador (C:\Users\...\uploads\logo.png)
            caminho_absoluto = os.path.abspath(os.path.join(os.getcwd(), caminho_relativo))
            
            # Injeta esse caminho no objeto para o template usar
            imobiliaria.logo_abspath = caminho_absoluto
        else:
            imobiliaria.logo_abspath = None

        dados_template = {
            "imobiliaria": imobiliaria,
            "locatario_nome": contrato.locatario_nome,
            "valor_aluguel": PDFService._format_currency(contrato.valor_aluguel),
            "valor_iptu": PDFService._format_currency(contrato.valor_iptu),
            "valor_condominio": PDFService._format_currency(contrato.valor_condominio),
            "prazo_meses": contrato.prazo_meses,
            "data_inicio": contrato.data_inicio.strftime("%d/%m/%Y")
        }

        env = PDFService._get_template_env()
        template = env.get_template("contrato_locacao.html")
        html_content = template.render(dados_template)

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content, dest=pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer