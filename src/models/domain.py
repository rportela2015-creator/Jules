from dataclasses import dataclass
from decimal import Decimal
from src.utils.math import ZERO, ONE

@dataclass
class ClassifiedProductInput:
    codigo_produto: str
    descricao: str
    ncm: str
    cst_ibs_cbs: str = "000"
    c_class_trib: str = "000001"
    quantidade: Decimal = Decimal("1")
    valor_bruto_item_entrada: Decimal = ZERO
    frete_seguro_despesas_entrada: Decimal = ZERO
    desconto_incondicional_entrada: Decimal = ZERO
    valor_ipi_entrada: Decimal = ZERO          # comerciante: IPI não recuperável -> custo
    valor_is_entrada: Decimal = ZERO           # IS na compra: irrecuperável -> custo
    v_cred_cbs_entrada: Decimal = ZERO         # total do lote
    v_cred_ibs_entrada: Decimal = ZERO
    v_cred_icms_entrada: Decimal = ZERO
    pis_cofins_entrada_info: Decimal = ZERO    # apenas informativo (NF-e 2026)
    p_red_cbs_produto: Decimal = ZERO
    p_red_ibs_produto: Decimal = ZERO
    # --- estoque de abertura (art. 381 LC 214/2025) ---
    estoque_abertura: bool = False
    regime_pis_cofins_2026: str = "nao_cumulativo"   # cumulativo | monofasico_st | nao_cumulativo
    origem: str = "nacional"                          # nacional | importado
    pis_cofins_importacao_pago_unit: Decimal = ZERO   # importado: efetivamente pago, sem adicional de COFINS


@dataclass
class SimulationParameters:
    ano_competencia: int = 2027
    aplicar_calendario_transicao: bool = True
    # mercadológicos
    margem_lucro_liquida_pct: Decimal = Decimal("20")       # sobre vProdLiq
    despesas_variaveis_venda_pct: Decimal = Decimal("5")
    base_despesas_variaveis: str = "preco_final"           # preco_final | vprodliq
    custo_fixo_rateado_unitario: Decimal = ZERO
    irpj_csll_pct: Decimal = ZERO                           # presumido comércio: 2,28 (1,2 IRPJ + 1,08 CSLL), sem adicional
    base_irpj_csll: str = "receita_bruta"                  # receita_bruta (preço final - IBS - CBS) | vprodliq
    # tributários de saída
    aliquota_icms_saida_pct: Decimal = Decimal("12")
    aliquota_is_saida_pct: Decimal = ZERO
    deducao_legal_base_iva: Decimal = ZERO
    incluir_iva_na_base_icms: bool = True                   # SEFA-PR Consulta 48/2026 (False = tese de liminar)
    # regime / entrada
    aproveitar_credito_iva_entrada: bool = True
    aproveitar_credito_icms_entrada: bool = True
    vprod_inclui_ibs_cbs: bool = False                      # NT 2026.008 v1.01 (30/10/2026): fora do vProd. v1.00: True
    estimar_iva_entrada_se_ausente: bool = True
    # crédito de estoque
    aliquota_credito_presumido_pct: Decimal = Decimal("9.25")
    modo_credito_estoque: str = "integral"                  # integral (CPC 16) | vp (CPC 12) | nenhum
    mes_apropriacao_credito: int = 1                        # 1..6 (limite legal: junho/2027)
    mes_venda: int = 1                                      # mês de 2027 em que a venda ocorre (fluxo de caixa)
    taxa_desconto_mensal_pct: Decimal = ZERO                # p/ VP das 12 parcelas
