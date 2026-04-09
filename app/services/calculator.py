import calendar
from datetime import date
from decimal import Decimal
from dateutil.relativedelta import relativedelta

class RescisaoService:
    
    @staticmethod
    def calcular_dias_proporcionais(data_desocupacao: date):
        """
        Retorna uma tupla (dias_usados, total_dias_no_mes).
        Ex: Se saiu dia 15 de Março, retorna (15, 31).
        """
        # monthrange retorna (dia_da_semana_da_estreia, total_de_dias_no_mes)
        _, total_dias_mes = calendar.monthrange(data_desocupacao.year, data_desocupacao.month)
        dias_usados = data_desocupacao.day
        return dias_usados, total_dias_mes

    @staticmethod
    def calcular_aluguel_proporcional(valor_mensal: float, data_desocupacao: date, modo_comercial: bool = False) -> float:
        """
        Calcula o valor do aluguel proporcional aos dias usados no mês de saída.
        """
        if not valor_mensal:
            return 0.0
            
        dias_usados, total_dias_mes = RescisaoService.calcular_dias_proporcionais(data_desocupacao)
        
        # Modo comercial usa base 30, caso contrário usa os dias reais do mês (28, 29, 30 ou 31)
        divisor = 30 if modo_comercial else total_dias_mes
        
        valor_diario = valor_mensal / divisor
        return round(valor_diario * dias_usados, 2)

    @staticmethod
    def calcular_encargo_proporcional(valor_mensal: float, data_desocupacao: date, modo_comercial: bool = False) -> float:
        """
        Calcula o valor proporcional de IPTU ou Condomínio.
        """
        # Reutiliza a lógica do aluguel já que o cálculo de dias é o mesmo
        return RescisaoService.calcular_aluguel_proporcional(valor_mensal, data_desocupacao, modo_comercial)

    @staticmethod
    def calcular_multa_proporcional(
        valor_aluguel: float,
        data_inicio: date,
        data_desocupacao: date,
        prazo_meses: int,
        multa_total_meses: int,
        isentar_multa: bool = False
    ) -> float:
        """
        Calcula a multa rescisória proporcional aos dias que faltam para 
        o término do contrato (Art. 4º da Lei 8.245/91).
        """
        
        # 1. Regra de Isenção (Sprint 9)
        if isentar_multa:
            return 0.0

        # 2. Determinar a data final teórica do contrato usando relativedelta
        data_fim_contrato = data_inicio + relativedelta(months=prazo_meses)

        # 3. Se a desocupação for após o fim do contrato, multa é zero
        if data_desocupacao >= data_fim_contrato:
            return 0.0

        # 4. Cálculo por DIAS (Precisão Máxima)
        prazo_total_dias = (data_fim_contrato - data_inicio).days
        dias_cumpridos = (data_desocupacao - data_inicio).days
        
        # Garante que não teremos valores negativos se a data de desocupação for retroativa
        dias_cumpridos = max(0, dias_cumpridos)
        dias_restantes = prazo_total_dias - dias_cumpridos

        # 5. Cálculo da Multa
        multa_cheia = valor_aluguel * multa_total_meses
        
        # Proporcionalidade: (Multa Total / Dias de Contrato) * Dias Restantes
        valor_multa_proporcional = (multa_cheia / prazo_total_dias) * dias_restantes

        return round(float(valor_multa_proporcional), 2)