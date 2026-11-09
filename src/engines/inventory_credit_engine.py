from decimal import Decimal
from typing import Any, Dict
from src.models.domain import ClassifiedProductInput, SimulationParameters
from src.utils.math import ZERO, ONE, r2, pc, fl

def credito_estoque_abertura(it: ClassifiedProductInput, p: SimulationParameters, custo_aquisicao_unit: Decimal) -> Dict[str, Any]:
    out: Dict[str, Any] = {"elegivel": False, "motivo": "", "credito_unit": ZERO, "vp_unit": ZERO, "cronograma": []}
    if not it.estoque_abertura:
        out["motivo"] = "item não é estoque de abertura"
        return out
    if it.regime_pis_cofins_2026 == "nao_cumulativo":
        out["motivo"] = "regime não cumulativo: crédito já apropriado na entrada (EFD-Contribuições) — sem crédito presumido"
        return out
    if not 1 <= p.mes_apropriacao_credito <= 6:
        raise ValueError("mes_apropriacao_credito deve estar entre 1 e 6 (apropriação até 30/06/2027).")
    cred = (it.pis_cofins_importacao_pago_unit if it.origem == "importado"
            else r2(custo_aquisicao_unit * pc(p.aliquota_credito_presumido_pct)))
    parcela = r2(cred / 12)
    t = pc(p.taxa_desconto_mensal_pct)
    cron, vp = [], ZERO
    for n in range(1, 13):
        mes = p.mes_apropriacao_credito + n                      # 1ª parcela: período seguinte ao da apropriação
        val = parcela if n < 12 else cred - parcela * 11          # última absorve resíduo
        cron.append({"mes_rel_jan2027": mes, "valor_unit": fl(val)})
        vp += val / ((ONE + t) ** mes)
    out.update(elegivel=True, credito_unit=cred, vp_unit=r2(vp), cronograma=cron,
               motivo="ok" + (" (importado: PIS/COFINS-Importação efetivamente pago)" if it.origem == "importado" else ""))
    return out
