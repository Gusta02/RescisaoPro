from datetime import date
import calendar
from decimal import Decimal

class RescisaoService:
    @staticmethod
    def calcular_dias_proporcionais(data_desocupacao: date):
        """Retorna quantos dias o inquilino usou e quantos dias o mês tem."""
        ultimo_dia_mes = calendar.monthrange(data_desocupacao.year, data_desocupacao.month)[1]
        dias_usados = data_desocupacao.day
        return dias_usados, ultimo_dia_mes

    @staticmethod
    def calcular_aluguel_proporcional(valor_mensal: Decimal, data_desocupacao: date, modo_comercial: bool = False):
        """
        Calcula o valor proporcional. 
        Se modo_comercial=True, divide sempre por 30. 
        Se False, divide pelos dias reais do mês.
        """
        dias_usados, total_dias_mes = RescisaoService.calcular_dias_proporcionais(data_desocupacao)
        
        divisor = Decimal(30) if modo_comercial else Decimal(total_dias_mes)
        valor_diario = valor_mensal / divisor
        
        return (valor_diario * Decimal(dias_usados)).quantize(Decimal("0.01"))

    @staticmethod
    def calcular_multa_proporcional(
        valor_aluguel: Decimal, 
        data_inicio: date, 
        data_desocupacao: date, 
        prazo_contrato_meses: int, 
        multa_total_meses: int
    ):
        """
        Calcula a multa proporcional aos meses restantes (Lei do Inquilinato).
        """
        # Cálculo simplificado de meses decorridos
        meses_decorridos = (data_desocupacao.year - data_inicio.year) * 12 + (data_desocupacao.month - data_inicio.month)
        
        # Se saiu após o prazo, não há multa
        if meses_decorridos >= prazo_contrato_meses:
            return Decimal("0.00")
            
        meses_restantes = prazo_contrato_meses - meses_decorridos
        multa_cheia = valor_aluguel * Decimal(multa_total_meses)
        
        valor_multa = (multa_cheia / Decimal(prazo_contrato_meses)) * Decimal(meses_restantes)
        return valor_multa.quantize(Decimal("0.01"))
    
    @staticmethod
    def calcular_encargo_proporcional(valor_mensal: float, data_desocupacao: date, modo_comercial: bool) -> float:
        """Calcula o valor proporcional de IPTU ou Condomínio baseado nos dias do mês de saída."""
        if not valor_mensal or valor_mensal <= 0:
            return 0.0
            
        dias_usados, dias_no_mes = RescisaoService.calcular_dias_proporcionais(data_desocupacao)
        
        if modo_comercial:
            return (valor_mensal / 30) * dias_usados
        return (valor_mensal / dias_no_mes) * dias_usados