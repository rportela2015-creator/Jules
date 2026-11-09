import xml.etree.ElementTree as ET
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Union

from src.exceptions import InvalidInputError


class InputDispatcher:
    @staticmethod
    def parse_input(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses XML string or Dictionary payload and standardizes the output.
        """
        if isinstance(data, str):
            try:
                # Try parsing as JSON first
                parsed_dict = json.loads(data)
                return InputDispatcher._process_dict(parsed_dict)
            except json.JSONDecodeError:
                # If not JSON, try parsing as XML
                return InputDispatcher._process_xml(data)
        elif isinstance(data, dict):
            return InputDispatcher._process_dict(data)
        else:
            raise InvalidInputError("Input must be a string (XML/JSON) or a dictionary.")

    @staticmethod
    def _process_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ncm = str(data.get('ncm') or data.get('NCM'))
            if not ncm or ncm.lower() == 'none':
                raise InvalidInputError("NCM is required in the input dictionary.")

            valor_base = Decimal(str(data.get('valor_base', 0))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # Allow default regime
            regime_vendedor = data.get('regime_vendedor', 'Lucro Real / Presumido')
            tipo_adquirente = data.get('tipo_adquirente', 'B2B')

            return {
                'ncm': ncm,
                'valor_base': valor_base,
                'regime_vendedor': regime_vendedor,
                'tipo_adquirente': tipo_adquirente
            }
        except Exception as e:
            raise InvalidInputError(f"Failed to process dictionary input: {str(e)}")

    @staticmethod
    def _process_xml(xml_string: str) -> Dict[str, Any]:
        try:
            root = ET.fromstring(xml_string)
            # Find namespaces if they exist
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

            # Simple heuristic for XML tags if namespace isn't correctly prefixed
            ncm_element = root.find('.//NCM')
            if ncm_element is None:
                ncm_element = root.find('.//nfe:NCM', ns)

            if ncm_element is None or not ncm_element.text:
                raise InvalidInputError("NCM tag not found or empty in XML.")

            ncm = str(ncm_element.text)

            vprod_element = root.find('.//vProd')
            if vprod_element is None:
                vprod_element = root.find('.//nfe:vProd', ns)

            valor_base_str = vprod_element.text if vprod_element is not None else '0'
            valor_base = Decimal(valor_base_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            return {
                'ncm': ncm,
                'valor_base': valor_base,
                # Default assumptions for XML, could be extracted from CRT / other tags
                'regime_vendedor': 'Lucro Real / Presumido',
                'tipo_adquirente': 'B2B'
            }

        except ET.ParseError as e:
            raise InvalidInputError(f"Failed to parse XML: {str(e)}")
        except Exception as e:
            raise InvalidInputError(f"Error processing XML: {str(e)}")
