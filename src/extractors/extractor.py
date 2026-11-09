import xml.etree.ElementTree as ET
from typing import Any, Dict
from src.models.domain import ClassifiedProductInput
from src.utils.math import dec, ONE

class InputExtractor:
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> ClassifiedProductInput:
        g = d.get
        return ClassifiedProductInput(
            codigo_produto=str(g("codigo_produto", "001")), descricao=str(g("descricao", "Produto")),
            ncm=str(g("ncm", "00000000")), cst_ibs_cbs=str(g("cst_ibs_cbs", "000")),
            c_class_trib=str(g("c_class_trib", "000001")), quantidade=dec(g("quantidade", 1)),
            valor_bruto_item_entrada=dec(g("valor_bruto_item_entrada")),
            frete_seguro_despesas_entrada=dec(g("frete_seguro_despesas_entrada")),
            desconto_incondicional_entrada=dec(g("desconto_incondicional_entrada")),
            valor_ipi_entrada=dec(g("valor_ipi_entrada")), valor_is_entrada=dec(g("valor_is_entrada")),
            v_cred_cbs_entrada=dec(g("v_cred_cbs_entrada")), v_cred_ibs_entrada=dec(g("v_cred_ibs_entrada")),
            v_cred_icms_entrada=dec(g("v_cred_icms_entrada")), pis_cofins_entrada_info=dec(g("pis_cofins_entrada_info")),
            p_red_cbs_produto=dec(g("p_red_cbs_produto")), p_red_ibs_produto=dec(g("p_red_ibs_produto")),
            estoque_abertura=bool(g("estoque_abertura", False)),
            regime_pis_cofins_2026=str(g("regime_pis_cofins_2026", "nao_cumulativo")),
            origem=str(g("origem", "nacional")),
            pis_cofins_importacao_pago_unit=dec(g("pis_cofins_importacao_pago_unit")),
        )

    @staticmethod
    def from_nfe_xml(xml_content: str, item_index: int = 0) -> ClassifiedProductInput:
        root = ET.fromstring(xml_content)
        ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

        def find(parent, tag):
            el = parent.find(f".//nfe:{tag}", ns)
            return el if el is not None else parent.find(f".//{tag}")

        def txt(parent, tag, default="0"):
            if parent is None:
                return default
            el = find(parent, tag)
            return el.text.strip() if (el is not None and el.text) else default

        dets = root.findall(".//nfe:det", ns) or root.findall(".//det")
        if item_index >= len(dets):
            raise ValueError(f"Item {item_index} não encontrado no XML.")
        det = dets[item_index]
        prod, imposto = find(det, "prod"), find(det, "imposto")
        ibscbs = find(imposto, "IBSCBS") if imposto is not None else None   # CST/pRed ESCOPADOS aqui (o protótipo pegava o CST do ICMS)
        v_ibs = dec(txt(ibscbs, "vIBS")) or (dec(txt(ibscbs, "vIBSUF")) + dec(txt(ibscbs, "vIBSMun")))
        q = dec(txt(prod, "qCom", "1"))
        return ClassifiedProductInput(
            codigo_produto=txt(prod, "cProd", "SEM_COD"), descricao=txt(prod, "xProd", "ITEM_XML"),
            ncm=txt(prod, "NCM", "00000000"), cst_ibs_cbs=txt(ibscbs, "CST", "000"),
            c_class_trib=txt(ibscbs, "cClassTrib", "000001"), quantidade=q if q > 0 else ONE,
            valor_bruto_item_entrada=dec(txt(prod, "vProd")),
            frete_seguro_despesas_entrada=dec(txt(prod, "vFrete")) + dec(txt(prod, "vSeg")) + dec(txt(prod, "vOutro")),
            desconto_incondicional_entrada=dec(txt(prod, "vDesc")),
            valor_ipi_entrada=dec(txt(imposto, "vIPI")), valor_is_entrada=dec(txt(imposto, "vIS")),
            v_cred_cbs_entrada=dec(txt(ibscbs, "vCBS")), v_cred_ibs_entrada=v_ibs,
            v_cred_icms_entrada=dec(txt(imposto, "vICMS")),
            pis_cofins_entrada_info=dec(txt(imposto, "vPIS")) + dec(txt(imposto, "vCOFINS")),
            p_red_cbs_produto=dec(txt(ibscbs, "pRedCBS")), p_red_ibs_produto=dec(txt(ibscbs, "pRedIBS")),
        )
