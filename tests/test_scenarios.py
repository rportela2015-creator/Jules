import pytest
from decimal import Decimal
import json

from src.ingress.input_dispatcher import InputDispatcher
from src.engines.tax_scenario_selector import TaxScenarioSelector
from src.exceptions import InvalidInputError

def test_xml_input():
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
    <nfe:nfeProc xmlns:nfe="http://www.portalfiscal.inf.br/nfe">
        <nfe:NFe>
            <nfe:infNFe>
                <nfe:det nItem="1">
                    <nfe:prod>
                        <nfe:cProd>12345</nfe:cProd>
                        <nfe:cEAN>SEM GTIN</nfe:cEAN>
                        <nfe:xProd>Tijolo Ceramico</nfe:xProd>
                        <nfe:NCM>69041000</nfe:NCM>
                        <nfe:CFOP>5102</nfe:CFOP>
                        <nfe:uCom>UN</nfe:uCom>
                        <nfe:qCom>1000.0000</nfe:qCom>
                        <nfe:vUnCom>1.5000</nfe:vUnCom>
                        <nfe:vProd>1500.00</nfe:vProd>
                    </nfe:prod>
                </nfe:det>
            </nfe:infNFe>
        </nfe:NFe>
    </nfe:nfeProc>
    """
    result = InputDispatcher.parse_input(xml_data)
    assert result['ncm'] == '69041000'
    assert result['valor_base'] == Decimal('1500.00')
    assert result['regime_vendedor'] == 'Lucro Real / Presumido'
    assert result['tipo_adquirente'] == 'B2B'

def test_json_input():
    json_data = json.dumps({
        "ncm": "25051000",
        "valor_base": 500.556
    })
    result = InputDispatcher.parse_input(json_data)
    assert result['ncm'] == '25051000'
    assert result['valor_base'] == Decimal('500.56')

def test_dict_input():
    dict_data = {
        "ncm": "25232910",
        "valor_base": "1200.00",
        "regime_vendedor": "Simples Nacional (Híbrido)",
        "tipo_adquirente": "B2B"
    }
    result = InputDispatcher.parse_input(dict_data)
    assert result['ncm'] == '25232910'
    assert result['valor_base'] == Decimal('1200.00')
    assert result['regime_vendedor'] == 'Simples Nacional (Híbrido)'
    assert result['tipo_adquirente'] == 'B2B'

def test_invalid_input():
    with pytest.raises(InvalidInputError):
        InputDispatcher.parse_input({"valor_base": 100})
    with pytest.raises(InvalidInputError):
        InputDispatcher.parse_input("<xml></xml>")

def test_scenario_a():
    data = {
        'ncm': '12345678',
        'valor_base': Decimal('100.00'),
        'regime_vendedor': 'Lucro Real / Presumido',
        'tipo_adquirente': 'B2C'
    }
    result = TaxScenarioSelector.select_scenario(data)
    flags = result['flags_fiscais']
    assert flags['cenario_identificado'] == 'Cenário A'
    assert flags['aproveitamento_credito'] is False
    assert flags['destaque_icms'] is True
    assert flags['iva_por_fora'] is True

def test_scenario_b():
    data = {
        'ncm': '12345678',
        'valor_base': Decimal('100.00'),
        'regime_vendedor': 'Lucro Real / Presumido',
        'tipo_adquirente': 'B2B'
    }
    result = TaxScenarioSelector.select_scenario(data)
    flags = result['flags_fiscais']
    assert flags['cenario_identificado'] == 'Cenário B'
    assert flags['aproveitamento_credito'] is True
    assert flags['destaque_icms'] is True
    assert flags['iva_por_fora'] is True

def test_scenario_c():
    data = {
        'ncm': '12345678',
        'valor_base': Decimal('100.00'),
        'regime_vendedor': 'Simples Nacional (Tradicional)',
        'tipo_adquirente': 'B2B' # Can be B2B or B2C
    }
    result = TaxScenarioSelector.select_scenario(data)
    flags = result['flags_fiscais']
    assert flags['cenario_identificado'] == 'Cenário C'
    assert flags['aproveitamento_credito'] is False
    assert flags['destaque_icms'] is False
    assert flags['iva_por_fora'] is True

def test_scenario_d():
    data = {
        'ncm': '12345678',
        'valor_base': Decimal('100.00'),
        'regime_vendedor': 'Simples Nacional (Híbrido)',
        'tipo_adquirente': 'B2B'
    }
    result = TaxScenarioSelector.select_scenario(data)
    flags = result['flags_fiscais']
    assert flags['cenario_identificado'] == 'Cenário D'
    assert flags['aproveitamento_credito'] is True
    assert flags['destaque_icms'] is False
    assert flags['iva_por_fora'] is True
