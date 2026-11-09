from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from enum import Enum

class ModalidadeICMS(Enum):
    NORMAL = "normal"
    ST_MVA = "st_mva"
    ANTECIPACAO = "antecipacao"
    DIFERIMENTO_PARCIAL = "diferimento_parcial"
    ISENTO = "isento"

class TipoDestinatarioSaida(Enum):
    CONTRIBUINTE = "contribuinte"
    CONSUMIDOR_FINAL = "consumidor_final"
    ORGAO_PUBLICO = "orgao_publico"

@dataclass
class ICMSParanaConfig:
    modalidade: ModalidadeICMS = ModalidadeICMS.NORMAL
    mva_original: Optional[Decimal] = None
    mva_ajustada: Optional[Decimal] = None
    reducao_base_icms: Optional[Decimal] = None
    cesta_basica_pr: bool = False
    fundo_pobreza: bool = False
    aliquota_interna_destino: Decimal = Decimal("19.5") # Alíquota padrão atual no PR
