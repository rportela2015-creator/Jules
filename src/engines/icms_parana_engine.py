from decimal import Decimal
from typing import Dict, Any, Tuple
from src.models.domain import ClassifiedProductInput, SimulationParameters
from src.models.parana import ICMSParanaConfig, ModalidadeICMS
from src.utils.math import r2, ZERO, pc

class ICMSParanaEngine:
    """Motor especialista do RICMS/PR."""

    # Exemplo de catálogo de produtos críticos PR (simplificado)
    CATALOGO_PRODUTOS_CRITICOS_PR = {
        "31052000": {"diferimento_parcial": True} # Exemplo de NCM que pode ter diferimento
    }

    @staticmethod
    def _aplicar_regras_parana(it: ClassifiedProductInput, p: SimulationParameters, config: ICMSParanaConfig, preco_base: Decimal) -> Tuple[Decimal, str]:
        # Logica especifica ICMS PR.
        # Por simplificacao, mantemos a logica padrão do pricing engine para o caso base.
        # Em producao isso faria lookup do ncm e aplicaria ST / antecipacao etc.
        aliquota = p.aliquota_icms_saida_pct
        obs = ""

        if config.modalidade == ModalidadeICMS.ISENTO:
            aliquota = ZERO
            obs = "Isento no PR"
        elif config.modalidade == ModalidadeICMS.DIFERIMENTO_PARCIAL or it.ncm in ICMSParanaEngine.CATALOGO_PRODUTOS_CRITICOS_PR:
            aliquota = Decimal("12") # Exemplo: 38,46% de redução para 12%
            obs = "Diferimento parcial no PR (12%)"
        elif config.cesta_basica_pr:
            aliquota = Decimal("7")
            obs = "Cesta Básica PR (7%)"

        return aliquota, obs
