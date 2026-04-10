from datetime import date, timedelta
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from app.models.core import Contrato, Rescisao
from dateutil.relativedelta import relativedelta

class ManagementService:
    @staticmethod
    def get_dashboard_summary(db: Session, imobiliaria_id: str):
        hoje = date.today()
        proximos_30_dias = hoje + timedelta(days=30)
        
        eventos = []

        # 1. ALERTAS DE REAJUSTE (Contratos que fazem aniversário este mês)
        # Filtramos contratos da imobiliária que iniciaram no mês atual em anos anteriores
        contratos_reajuste = db.query(Contrato).filter(
            Contrato.imobiliaria_id == imobiliaria_id,
            extract('month', Contrato.data_inicio) == hoje.month
        ).all()



        for c in contratos_reajuste:
            if c.data_inicio.year < hoje.year:
                eventos.append({
                    "data": hoje.replace(day=min(c.data_inicio.day, 28)), # Evita erro em meses curtos
                    "tipo": "REAJUSTE",
                    "titulo": f"Reajuste Anual: {c.locatario_nome}",
                    "descricao": f"O contrato completou {(hoje.year - c.data_inicio.year)} ano(s). Verifique o índice de reajuste.",
                    "prioridade": "ALTA",
                    "metadata": {"contrato_id": str(c.id)}
                })

        # 2. VENCIMENTOS DE CONTRATO (Final do prazo contratual)
        todos_contratos = db.query(Contrato).filter(Contrato.imobiliaria_id == imobiliaria_id).all()
        for c in todos_contratos:
            data_fim = c.data_inicio + relativedelta(months=c.prazo_meses)
            if hoje <= data_fim <= proximos_30_dias:
                eventos.append({
                    "data": data_fim,
                    "tipo": "VENCIMENTO",
                    "titulo": f"Vencimento: {c.locatario_nome}",
                    "descricao": "O prazo de locação encerra em breve. Negociar renovação ou preparar vistoria.",
                    "prioridade": "URGENTE",
                    "metadata": {"contrato_id": str(c.id)}
                })

        # 3. DESOCUPAÇÕES AGENDADAS (Rescisões em aberto para os próximos 7 dias)
        prox_semana = hoje + timedelta(days=7)
        rescisoes_agendadas = db.query(Rescisao).join(Contrato).filter(
            Contrato.imobiliaria_id == imobiliaria_id,
            Rescisao.data_desocupacao >= hoje,
            Rescisao.data_desocupacao <= prox_semana,
            Rescisao.status != "FINALIZADO"
        ).all()

        for r in rescisoes_agendadas:
            eventos.append({
                "data": r.data_desocupacao,
                "tipo": "DESOCUPACAO",
                "titulo": f"Saída: {r.contrato.locatario_nome}",
                "descricao": f"Desocupação agendada. Status atual: {r.status}.",
                "prioridade": "MEDIA",
                "metadata": {"rescisao_id": str(r.id)}
            })

        eventos_formatados = sorted(eventos, key=lambda x: x['data'])
        
        return {
            "total_eventos": len(eventos_formatados),
            "eventos": eventos_formatados
        }
    @staticmethod
    def get_business_kpis(db: Session, imobiliaria_id: str):
        # 1. Total de Aluguel sob Gestão (Soma de todos os contratos ativos)
        total_sob_gestao = db.query(func.sum(Contrato.valor_aluguel)).filter(
            Contrato.imobiliaria_id == imobiliaria_id
        ).scalar() or 0

        # 2. Volume de Rescisões em Aberto (Rascunhos ou Aguardando)
        rescisoes_pendentes = db.query(Rescisao).join(Contrato).filter(
            Contrato.imobiliaria_id == imobiliaria_id,
            Rescisao.status != "FINALIZADO"
        ).count()

        # 3. Ticket Médio de Aluguel
        qtd_contratos = db.query(Contrato).filter(Contrato.imobiliaria_id == imobiliaria_id).count()
        ticket_medio = total_sob_gestao / qtd_contratos if qtd_contratos > 0 else 0

        return {
            "total_aluguel_sob_gestao": float(total_sob_gestao),
            "total_contratos_ativos": qtd_contratos,
            "rescisoes_em_curso": rescisoes_pendentes,
            "ticket_medio": float(ticket_medio)
        }