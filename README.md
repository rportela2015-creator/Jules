# Agente de Custeio, Precificação e Simulação Tributária Pós-Reforma (IVA Dual + ICMS-PR)

## Arquitetura
- **src/models**: Dataclasses de domínio (Produto, Parâmetros, Configurações do PR).
- **src/utils**: Utilitários matemáticos com `Decimal` para evitar perdas de precisão.
- **src/persistence**: Persistência atômica das alíquotas de referência em JSON.
- **src/extractors**: Ingestão de dados (Dicionários, XML de NF-e).
- **src/engines**: Motores de cálculo isolados (Crédito de Estoque, ICMS-PR, Pricing Agent).
- **tests**: Suíte de testes validando os cálculos baseados na NT e manuais de reforma.

## Rodando os testes
```bash
pytest tests/
```
