import os
from io import BytesIO
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from app.models.core import Rescisao, Contrato
from fastapi import HTTPException

class PDFService:
    @staticmethod
    def gerar_pdf_rescisao(db: Session, rescisao_id: str):
        # 1. Busca os dados no banco
        rescisao = db.query(Rescisao).filter(Rescisao.id == rescisao_id).first()
        if not rescisao:
            raise HTTPException(status_code=404, detail="Rescisão não encontrada")
        
        contrato = db.query(Contrato).filter(Contrato.id == rescisao.contrato_id).first()

        # 2. Prepara os dados para o template
        total_debito = sum(item.valor for item in rescisao.itens if item.tipo == "DEBITO")
        total_credito = sum(item.valor for item in rescisao.itens if item.tipo == "CREDITO")
        total_final = total_debito - total_credito

        dados_template = {
            "locatario_nome": contrato.locatario_nome,
            "data_desocupacao": rescisao.data_desocupacao.strftime("%d/%m/%Y"),
            "itens": rescisao.itens,
            "total_final": f"{total_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "imobiliaria": contrato.imobiliaria.nome_fantasia
        }

        # 3. Carrega o template Jinja2
        # Certifique-se de que a pasta 'templates' existe na raiz de 'app'
        template_path = os.path.join(os.path.dirname(__file__), "..", "template")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("termo_rescisao.html")
        html_content = template.render(dados_template)

        # 4. Converte HTML para PDF em memória
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

        dados_template = {
            "imobiliaria_nome": contrato.imobiliaria.nome_fantasia,
            "locatario_nome": contrato.locatario_nome,
            "valor_aluguel": f"{contrato.valor_aluguel:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "valor_iptu": contrato.valor_iptu,
            "valor_condominio": contrato.valor_condominio,
            "prazo_meses": contrato.prazo_meses,
            "data_inicio": contrato.data_inicio.strftime("%d/%m/%Y")
        }

        template_path = os.path.join(os.path.dirname(__file__), "..", "template")
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("contrato_locacao.html")
        html_content = template.render(dados_template)

        pdf_buffer = BytesIO()
        pisa.CreatePDF(html_content, dest=pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer