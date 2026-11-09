from typing import Dict, Any


class TaxScenarioSelector:
    @staticmethod
    def select_scenario(input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determina os parâmetros operacionais com base no regime do vendedor e tipo de adquirente.

        Cenários esperados:
        A: Lucro Real / Presumido -> B2C
        B: Lucro Real / Presumido -> B2B
        C: Simples Nacional (Tradicional) -> B2C/B2B
        D: Simples Nacional (Híbrido/LC 214) -> B2B
        """
        regime_vendedor = input_data.get('regime_vendedor', 'Lucro Real / Presumido')
        tipo_adquirente = input_data.get('tipo_adquirente', 'B2B')

        flags = {
            'aproveitamento_credito': False,
            'destaque_icms': False,
            'iva_por_fora': True, # IVA Dual sempre por fora
            'cenario_identificado': 'Desconhecido'
        }

        # Cenário A: Lucro Real / Presumido -> Consumidor Final (B2C)
        if regime_vendedor == 'Lucro Real / Presumido' and tipo_adquirente in ('B2C', 'Não Contribuinte'):
            flags['cenario_identificado'] = 'Cenário A'
            flags['aproveitamento_credito'] = False
            flags['destaque_icms'] = True

        # Cenário B: Lucro Real / Presumido -> Empresa Contribuinte (B2B)
        elif regime_vendedor == 'Lucro Real / Presumido' and tipo_adquirente == 'B2B':
            flags['cenario_identificado'] = 'Cenário B'
            flags['aproveitamento_credito'] = True
            flags['destaque_icms'] = True

        # Cenário C: Simples Nacional (Tradicional) -> B2C ou B2B
        elif regime_vendedor == 'Simples Nacional (Tradicional)':
            flags['cenario_identificado'] = 'Cenário C'
            flags['aproveitamento_credito'] = False # Sem transferência plena de créditos do IVA Dual
            flags['destaque_icms'] = False

        # Cenário D: Simples Nacional (Híbrido) -> Empresa Contribuinte B2B
        elif regime_vendedor == 'Simples Nacional (Híbrido)' and tipo_adquirente == 'B2B':
            flags['cenario_identificado'] = 'Cenário D'
            flags['aproveitamento_credito'] = True # Permite destaque e transferência de créditos (LC 214/2025)
            flags['destaque_icms'] = False # Normalmente ICMS fica na guia unificada, a não ser que exceda limite

        else:
            flags['cenario_identificado'] = f'Não Mapeado ({regime_vendedor} -> {tipo_adquirente})'

        return {**input_data, 'flags_fiscais': flags}
