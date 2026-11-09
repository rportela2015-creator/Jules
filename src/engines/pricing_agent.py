from decimal import Decimal
from typing import Any, Dict, List, Tuple
from src.models.domain import ClassifiedProductInput, SimulationParameters
from src.persistence.store import TaxPersistentStore
from src.engines.inventory_credit_engine import credito_estoque_abertura
from src.utils.math import ZERO, ONE, r2, pc, fl, dec

# CALENDÁRIO DE TRANSIÇÃO (valores em %)
_IBS_FRACAO = {2029: Decimal("0.1"), 2030: Decimal("0.2"), 2031: Decimal("0.3"), 2032: Decimal("0.4")}
_ICMS_FATOR = {2029: Decimal("0.9"), 2030: Decimal("0.8"), 2031: Decimal("0.7"), 2032: Decimal("0.6")}

def aliquotas_ano(ano: int, cbs_ref: Decimal, ibs_ref: Decimal) -> Tuple[Decimal, Decimal, Decimal, str]:
    if ano < 2027:
        raise ValueError("Simulação cobre 2027+. Em 2026 PIS/COFINS seguem vigentes e IBS/CBS são só teste.")
    if ano <= 2028:
        return max(ZERO, cbs_ref - Decimal("0.1")), Decimal("0.1"), ONE, "2027-28: CBS = ref - 0,1 p.p.; IBS 0,1% (0,05 UF + 0,05 mun.); ICMS integral"
    if ano <= 2032:
        return cbs_ref, ibs_ref * _IBS_FRACAO[ano], _ICMS_FATOR[ano], f"{ano}: IBS = {int(_IBS_FRACAO[ano]*100)}% da ref.; ICMS a {int(_ICMS_FATOR[ano]*100)}% da alíquota"
    return cbs_ref, ibs_ref, ZERO, "2033+: IBS pleno; ICMS extinto"

def _coef(a: Decimal, s: Decimal, ci: Decimal, ded: Decimal, dentro: bool) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    if dentro:
        k, m = (1 + s) * (1 + ci) / (1 - a), -ci * ded / (1 - a)
    else:
        k, m = (1 + s) * (1 / (1 - a) + ci), -ci * ded
    return k, m, k - ci * (1 + s), m + ci * ded

def _solve_vl(custo: Decimal, mg: Decimal, dv: Decimal, ir: Decimal, base_dv: str, base_ir: str,
              k: Decimal, m: Decimal, kr: Decimal, mr: Decimal) -> Decimal:
    dP = dv if base_dv == "preco_final" else ZERO
    dL = dv - dP
    irR = ir if base_ir == "receita_bruta" else ZERO
    irL = ir - irR
    den = 1 - mg - dL - irL - dP * k - irR * kr
    if den <= 0:
        raise ValueError("Margem + despesas + IRPJ/CSLL inviáveis: nenhum preço fecha a conta (denominador <= 0).")
    return (custo + dP * m + irR * mr) / den

class TaxPricingAgent:
    def __init__(self, store: TaxPersistentStore):
        self.store = store

    def simulate_resale_pricing(self, item: ClassifiedProductInput, params: SimulationParameters,
                                modo: str = "resumido") -> Dict[str, Any]:
        if modo not in ("resumido", "detalhado"):
            raise ValueError("modo deve ser 'resumido' ou 'detalhado'.")
        full = self._calc(item, params)
        return full if modo == "detalhado" else self._resumo(full)

    def _calc(self, it: ClassifiedProductInput, p: SimulationParameters) -> Dict[str, Any]:
        self._validate(it, p)
        alertas: List[str] = []
        cbs_ref, ibs_ref = self.store.cbs_pct, self.store.ibs_pct
        if p.aplicar_calendario_transicao:
            cbs_n, ibs_n, icms_fator, nota_cal = aliquotas_ano(p.ano_competencia, cbs_ref, ibs_ref)
        else:
            cbs_n, ibs_n, icms_fator, nota_cal = cbs_ref, ibs_ref, ONE, "calendário desligado: referência usada como efetiva"
            alertas.append("Calendário de transição desligado: alíquotas de referência aplicadas como efetivas.")
        c = pc(cbs_n) * (1 - pc(it.p_red_cbs_produto))
        i = pc(ibs_n) * (1 - pc(it.p_red_ibs_produto))
        a = pc(p.aliquota_icms_saida_pct) * icms_fator
        s = pc(p.aliquota_is_saida_pct)
        q = it.quantidade

        # MOTOR 1: custeio de entrada
        base = it.valor_bruto_item_entrada + it.frete_seguro_despesas_entrada - it.desconto_incondicional_entrada
        cred_cbs, cred_ibs = it.v_cred_cbs_entrada, it.v_cred_ibs_entrada
        iva_por_fora = not p.vprod_inclui_ibs_cbs
        estimado = False
        if (not it.estoque_abertura) and p.estimar_iva_entrada_se_ausente and cred_cbs == 0 and cred_ibs == 0:
            base_iva = base - it.v_cred_icms_entrada
            cred_cbs, cred_ibs, iva_por_fora, estimado = r2(base_iva * c), r2(base_iva * i), True, True
            alertas.append("IBS/CBS de entrada ESTIMADOS pelas alíquotas do ano; use o valor destacado na NF-e quando houver.")
        desembolso = base + it.valor_ipi_entrada + it.valor_is_entrada + ((cred_cbs + cred_ibs) if iva_por_fora else ZERO)
        rec_iva = (cred_cbs + cred_ibs) if p.aproveitar_credito_iva_entrada else ZERO
        rec_icms = it.v_cred_icms_entrada if p.aproveitar_credito_icms_entrada else ZERO
        custo_pre = r2((desembolso - rec_iva - rec_icms) / q)

        cr = credito_estoque_abertura(it, p, custo_pre)
        if it.estoque_abertura and not cr["elegivel"]:
            alertas.append(f"Sem crédito de estoque: {cr['motivo']}.")
        aplicado = {"integral": cr["credito_unit"], "vp": cr["vp_unit"], "nenhum": ZERO}[p.modo_credito_estoque]
        custo_liq = custo_pre - aplicado
        custo_base = custo_liq + p.custo_fixo_rateado_unitario

        # MOTOR 2: preço líquido (vProdLiq)
        mg, dv, ir = pc(p.margem_lucro_liquida_pct), pc(p.despesas_variaveis_venda_pct), pc(p.irpj_csll_pct)
        ded = p.deducao_legal_base_iva
        k, m, kr, mr = _coef(a, s, c + i, ded, p.incluir_iva_na_base_icms)
        vl = r2(_solve_vl(custo_base, mg, dv, ir, p.base_despesas_variaveis, p.base_irpj_csll, k, m, kr, mr))
        if (1 + s) * vl < ded:
            raise ValueError("Dedução legal maior que a base de IBS/CBS: revise deducao_legal_base_iva.")

        # MOTOR 3: tributos de saída
        v_is = r2(vl * s)
        bc_iva = vl + v_is - ded
        v_cbs, v_ibs = r2(bc_iva * c), r2(bc_iva * i)
        if a > 0:
            if p.incluir_iva_na_base_icms:
                bc_icms = r2((vl + v_is + v_cbs + v_ibs) / (1 - a)); preco = bc_icms
            else:
                bc_icms = r2((vl + v_is) / (1 - a)); preco = bc_icms + v_cbs + v_ibs
            v_icms = r2(bc_icms * a)
        else:
            bc_icms, v_icms, preco = ZERO, ZERO, vl + v_is + v_cbs + v_ibs

        # Resultado econômico realizado
        dv_val = r2(dv * (preco if p.base_despesas_variaveis == "preco_final" else vl))
        rb = preco - v_cbs - v_ibs
        ir_val = r2(ir * (rb if p.base_irpj_csll == "receita_bruta" else vl))
        lucro = vl - custo_base - dv_val - ir_val
        mc_unit = vl - custo_liq - dv_val - ir_val

        def _preco_aprox(cst: Decimal) -> Decimal:
            return r2(k * _solve_vl(cst, ZERO, dv, ir, p.base_despesas_variaveis, p.base_irpj_csll, k, m, kr, mr) + m)

        piso_zero = _preco_aprox(custo_base)
        piso_contrib = _preco_aprox(custo_liq)

        # Apuração e caixa
        cu_cbs = r2(cred_cbs / q) if p.aproveitar_credito_iva_entrada else ZERO
        cu_ibs = r2(cred_ibs / q) if p.aproveitar_credito_iva_entrada else ZERO
        cu_icms = r2(it.v_cred_icms_entrada / q) if p.aproveitar_credito_icms_entrada else ZERO
        cbs_liq, ibs_liq, icms_liq = v_cbs - cu_cbs, v_ibs - cu_ibs, v_icms - cu_icms
        cred_est = cr["credito_unit"]
        quotas_disp = max(0, min(12, p.mes_venda - p.mes_apropriacao_credito)) if cr["elegivel"] else 0
        disp = r2(cred_est * Decimal(quotas_disp) / 12)
        cbs_caixa = max(ZERO, cbs_liq - disp)
        cbs_econ = cbs_liq - cred_est

        if p.incluir_iva_na_base_icms:
            alertas.append("ICMS 'por dentro' com IBS/CBS/IS na base (SEFA-PR Consulta 48/2026); outras UFs/liminares podem divergir.")
        if p.irpj_csll_pct == pc(3.08) * 100:
            alertas.append("IRPJ/CSLL 3,08% não corresponde ao presumido de comércio (2,28%, sem adicional) — confirme a premissa.")
        if cr["elegivel"] and p.modo_credito_estoque == "integral":
            alertas.append(f"Crédito de estoque abatido do custo pelo valor nominal; caixa só libera 1/12 por mês a partir do mês {p.mes_apropriacao_credito + 1}. VP = {fl(cr['vp_unit'])}.")
        if cr["elegivel"]:
            alertas.append("Devolução de item do estoque de abertura estorna o crédito presumido proporcional (art. 381).")
        if abs(lucro / vl - mg) > Decimal("0.0005"):
            alertas.append(f"Margem realizada {fl(lucro / vl * 100)}% difere do alvo por arredondamento fiscal.")

        return {
            "item": {"codigo": it.codigo_produto, "descricao": it.descricao, "ncm": it.ncm, "cst": it.cst_ibs_cbs, "cClassTrib": it.c_class_trib},
            "ano": p.ano_competencia, "calendario": nota_cal,
            "aliquotas_efetivas_pct": {"cbs": fl(c * 100), "ibs": float(round(i * 100, 4)), "icms": fl(a * 100), "is": fl(s * 100)},
            "entrada": {"desembolso_unit": fl(desembolso / q), "ibs_cbs_estimado": estimado, "iva_por_fora_na_nf": iva_por_fora,
                        "credito_cbs_unit": fl(cu_cbs), "credito_ibs_unit": fl(cu_ibs), "credito_icms_unit": fl(cu_icms),
                        "custo_antes_credito_estoque": fl(custo_pre), "credito_estoque": {
                            "elegivel": cr["elegivel"], "motivo": cr["motivo"], "nominal": fl(cred_est), "valor_presente": fl(cr["vp_unit"]),
                            "aplicado_no_custo": fl(aplicado), "modo": p.modo_credito_estoque, "cronograma": cr["cronograma"]},
                        "custo_liquido": fl(custo_liq), "custo_fixo_rateado": fl(p.custo_fixo_rateado_unitario), "custo_base": fl(custo_base)},
            "preco": {"vProdLiq": fl(vl), "vIS": fl(v_is), "vBC_IBS_CBS": fl(bc_iva), "vCBS": fl(v_cbs), "vIBS": fl(v_ibs),
                      "vBC_ICMS": fl(bc_icms), "vICMS": fl(v_icms), "preco_final": fl(preco),
                      "markup_sobre_custo_liquido": float(round(preco / custo_liq, 4)) if custo_liq > 0 else None},
            "resultado": {"despesas_variaveis": fl(dv_val), "irpj_csll": fl(ir_val), "lucro_liquido": fl(lucro),
                          "margem_realizada_pct": fl(lucro / vl * 100), "margem_contribuicao_unit": fl(mc_unit),
                          "indice_margem_contribuicao_pct": fl(mc_unit / vl * 100),
                          "preco_piso_lucro_zero_aprox": fl(piso_zero), "preco_piso_contribuicao_aprox": fl(piso_contrib),
                          "carga_indireta_pct_do_preco": fl((v_cbs + v_ibs + v_icms + v_is) / preco * 100)},
            "apuracao_caixa": {"cbs_liquido_corrente": fl(cbs_liq), "ibs_liquido_corrente": fl(ibs_liq), "icms_liquido": fl(icms_liq),
                               "cbs_economico_apos_credito_estoque": fl(cbs_econ), "cbs_caixa_no_mes_da_venda": fl(cbs_caixa),
                               "credito_estoque_disponivel_no_mes": fl(disp), "retencao_split_payment_ivA": fl(v_cbs + v_ibs),
                               "entrada_liquida_conta": fl(preco - v_cbs - v_ibs),
                               "obs": "Crédito de estoque é consumido na apuração agregada da empresa; visão por unidade é aproximação."},
            "alertas": alertas,
        }

    @staticmethod
    def _resumo(r: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "item": f"{r['item']['codigo']} — {r['item']['descricao']}", "ano": r["ano"],
            "custo_liquido": r["entrada"]["custo_liquido"], "vProdLiq": r["preco"]["vProdLiq"],
            "preco_final": r["preco"]["preco_final"],
            "tributos_saida": {k: r["preco"][k] for k in ("vCBS", "vIBS", "vICMS", "vIS")},
            "lucro_liquido": r["resultado"]["lucro_liquido"], "margem_realizada_pct": r["resultado"]["margem_realizada_pct"],
            "preco_piso_lucro_zero": r["resultado"]["preco_piso_lucro_zero_aprox"],
            "cbs_a_recolher_caixa_mes_venda": r["apuracao_caixa"]["cbs_caixa_no_mes_da_venda"],
            "alertas": r["alertas"][:3] + (["… (+%d; use modo='detalhado')" % (len(r["alertas"]) - 3)] if len(r["alertas"]) > 3 else []),
        }

    @staticmethod
    def _validate(it: ClassifiedProductInput, p: SimulationParameters) -> None:
        if it.quantidade <= 0:
            raise ValueError("quantidade deve ser > 0")
        if not (0 <= pc(p.aliquota_icms_saida_pct) * 100 < 100):
            raise ValueError("ICMS fora de [0,100)")
        if p.base_despesas_variaveis not in ("preco_final", "vprodliq") or p.base_irpj_csll not in ("receita_bruta", "vprodliq"):
            raise ValueError("base_despesas_variaveis / base_irpj_csll inválidas")
        if p.modo_credito_estoque not in ("integral", "vp", "nenhum"):
            raise ValueError("modo_credito_estoque inválido")
        if p.deducao_legal_base_iva < 0:
            raise ValueError("deducao_legal_base_iva < 0")
