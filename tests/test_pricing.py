import os
import tempfile
from decimal import Decimal
import pytest
from src.persistence.store import TaxPersistentStore
from src.engines.pricing_agent import TaxPricingAgent
from src.extractors.extractor import InputExtractor
from src.models.domain import SimulationParameters
from src.utils.math import ZERO

def test_selftest_manual():
    # Selftest com as premissas do manual (CBS 8,8 / IBS 0,1 sem calendário)
    st_manual = TaxPersistentStore(os.path.join(tempfile.gettempdir(), "iva_manual.json"))
    st_manual.set_persistent_rates(8.8, 0.1, user_override=True)

    ag = TaxPricingAgent(st_manual)
    it = InputExtractor.from_dict({"codigo_produto": "T", "descricao": "Teste manual", "valor_bruto_item_entrada": 100,
                                   "v_cred_icms_entrada": 12, "estoque_abertura": True, "regime_pis_cofins_2026": "cumulativo"})
    p = SimulationParameters(aplicar_calendario_transicao=False, despesas_variaveis_venda_pct=Decimal("5"),
                             base_despesas_variaveis="vprodliq", irpj_csll_pct=ZERO, aliquota_icms_saida_pct=Decimal("12"))
    r = ag._calc(it, p)

    assert r["entrada"]["custo_antes_credito_estoque"] == 88.0
    assert r["entrada"]["credito_estoque"]["nominal"] == 8.14
    assert r["entrada"]["custo_liquido"] == 79.86
    assert r["preco"]["vProdLiq"] == 106.48
    assert r["preco"]["preco_final"] == 131.77
    assert r["resultado"]["lucro_liquido"] == 21.3

def test_caso1():
    store = TaxPersistentStore(os.path.join(tempfile.gettempdir(), "iva_ref.json"))
    store.set_persistent_rates(8.8, 17.7, user_override=True)
    ag = TaxPricingAgent(store)

    c1 = InputExtractor.from_dict({"codigo_produto": "SKU-7214", "descricao": "Vergalhão CA-50", "ncm": "72142000",
                                   "valor_bruto_item_entrada": 100, "v_cred_icms_entrada": 12})
    p1 = SimulationParameters(custo_fixo_rateado_unitario=Decimal("7"), irpj_csll_pct=Decimal("2.28"))
    r = ag._calc(c1, p1)
    assert r["ano"] == 2027
    assert r["entrada"]["custo_antes_credito_estoque"] == 88.0

def test_xml_extracao():
    xml = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><NFe><infNFe versao="4.00"><det nItem="1">
      <prod><cProd>INS-AGRO-01</cProd><xProd>Fertilizante NPK</xProd><NCM>31052000</NCM><qCom>10.0000</qCom><vProd>2212.00</vProd></prod>
      <imposto><ICMS><ICMS00><CST>00</CST><vBC>2212.00</vBC><pICMS>4.00</pICMS><vICMS>88.48</vICMS></ICMS00></ICMS>
      <IBSCBS><CST>200</CST><cClassTrib>200030</cClassTrib><gIBSCBS><vBC>2000.00</vBC><pRedCBS>60.00</pRedCBS><vCBS>70.40</vCBS>
      <pRedIBS>60.00</pRedIBS><vIBS>141.60</vIBS></gIBSCBS></IBSCBS></imposto></det></infNFe></NFe></nfeProc>"""
    c3 = InputExtractor.from_nfe_xml(xml)
    assert c3.cst_ibs_cbs == "200"
    assert c3.p_red_cbs_produto == Decimal("60.00")
    assert c3.v_cred_cbs_entrada == Decimal("70.40")
