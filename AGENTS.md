# AGENT.md - Diretrizes de Aperfeiçoamento, Padrões e Boas Práticas

Este documento define o padrão operacional, a arquitetura de engenharia e as regras de robustez para agentes de IA atuando no ecossistema de desenvolvimento de motores fiscais, contábeis e de precificação da Portela Contabilidade, sob a égide da Reforma Tributária (LC nº 214/2025, LC nº 227/2026, MP nº 1.399/2026 e RICMS/PR)[cite: 1, 37].

---

## 1. Princípios Fundamentais de Engenharia e Matemática Fiscal

1. **Precisão Absoluta em Ponto Fixo (`decimal.Decimal`):**
   * **Proibido o uso de `float`** para cálculos monetários, bases de cálculo, alíquotas e tributos.
   * Toda a aritmética fiscal deve ser executada obrigatoriamente utilizando a biblioteca `decimal.Decimal` com arredondamento estrito `ROUND_HALF_UP` (`decimal.ROUND_HALF_UP`).
   * Casas decimais padronizadas: **2 casas** para valores em Reais (R$) e **4 casas** para percentuais de MVA Ajustada, reduções e alíquotas fracionadas. * **Estilo Direto e Assertivo:** Responda com foco absoluto no conteúdo técnico. Sem saudações, preâmbulos, recapitulações ou encerramentos protocolares (*vá direto ao ponto*).
* **Idioma:** Responder estritamente em **Português do Brasil (PT-BR)**, exceto para blocos de código, funções, comandos de terminal ou sintaxes originais de ferramentas.
* **Resolução Pragmática de Variáveis:** Se faltar alguma premissa secundária ou variável técnica, **nunca trave por perguntas desnecessárias**. Adote a premissa mais lógica, declare-a explicitamente no início e conclua a execução. Pergunte ao usuário apenas se a ambiguidade inviabilizar a resposta de forma cirúrgica.
* **Mitigação de Incertezas e Erros:**
  * Dados não verificáveis (preços pontuais, versões específicas de bibliotecas, jurisprudências voláteis ou normas em trâmite) devem ser explicitamente sinalizados como **estimativas**, jamais apresentados como verdades absolutas.
  * Caso o usuário apresente uma premissa conceitualmente ou tecnicamente errada em sua pergunta, **corrija-a antes de iniciar a resposta**, independentemente da profundidade do erro.


2. **Isolamento Algébrico de Tributos ("Por Fora" vs. "Por Dentro"):**
   * Os tributos do IVA Dual (`IS`, `CBS`, `IBS`) são calculados estritamente **"por fora"**, incidem em cascata controlada sobre o valor líquido do produto (`vProdLiq`) e **não compõem** a base um do outro na origem[cite: 3].
   * O **ICMS** estadual do Paraná obedece ao *gross-up* regulamentar ("por dentro"), integrando a base de cálculo mediante a composição com o IVA Dual conforme o entendimento da Consulta SEFA/PR nº 48/2026 e da NT 2026.008, salvo em cenários de liminar judicial expressamente parametrizados[cite: 22, 33].

3. **Imutabilidade e Persistência de Alíquotas de Referência:**
   * As alíquotas de referência da CBS e do IBS devem ser lidas de um repositório persistente local (`TaxPersistentStore` / `tax_state_config.json`).
   * **Trava de Segurança:** Uma vez gravadas, nenhuma rotina automática de atualização de XML ou script de simulação pode sobrescrever tais valores, a menos que o usuário invoque explicitamente a flag de sobrescrita (`user_override=True`).

---

## 2. Arquitetura Modular do Repositório (Padrão de Código Limpo)

O código deve seguir rigorosamente a separação de responsabilidades em pacotes desacoplados:

```text
├── src/
│   ├── models/           # Dataclasses e Enums (Entidades de domínio imutáveis)
│   ├── persistence/      # Gerenciamento atômico de estados e JSON (TaxPersistentStore)
│   ├── extractors/       # Ingestão de dicionários e parsers XML de NF-e (NT 2025.002 / 2026.008)
│   └── engines/          # Motores de cálculo especializados:
│       ├── inventory_credit_engine.py  # Crédito de estoque de transição (31/12/2026) e amortização 12x
│       ├── icms_parana_engine.py       # Motor RICMS/PR (ST, MVA Ajustada, PMPF, Diferimento Parcial B2B)
│       └── pricing_agent.py            # Orquestrador central de custeio, Mark-up e Split Payment
├── tests/                # Suíte completa de testes unitários com pytest / unittest
└── pyproject.toml        # Configuração de dependências e metadados do projeto 3. Diretrizes de Qualidade, Testes e Resiliência (Boas Práticas)Cobertura de Testes Automatizados:Toda nova regra fiscal incorporada ao motor (ex: novos convênios do CONFAZ, alterações de MVA ou novas notas técnicas do ENCAT) deve vir acompanhada de um caso de teste unitário na pasta tests/.Os testes devem validar simulações ponta a ponta (Entrada $\rightarrow$ Custeio $\rightarrow$ Precificação $\rightarrow$ Saída $\rightarrow$ Fechamento de NF-e).Tratamento Cirúrgico de Exceções:Valide pré-condições de entrada (ex: soma de mark-up e despesas variáveis não pode ser $\ge 100\%$).Lance exceções tipadas e descritivas (ValueError, TaxEngineError) quando houver inconsistências em chaves de NCM, CST ou cClassTrib desconhecidos.Auditoria e Rastreabilidade de Memória de Cálculo:Os dicionários de saída gerados pelo agente devem retornar sempre a memória de cálculo textual detalhada (fórmulas aplicadas, bases de cálculo e dispositivos legais), facilitando a conferência pelo auditor fiscal ou contador responsável.4. Instruções Operacionais para Agentes Autônomos (Jules / IA)Jamais utilize suposições sobre alíquotas ou regras genéricas de outros estados sem respaldo na legislação do Paraná (RICMS/PR) ou nas Leis Complementares da Reforma Tributária (LC 214/2025 e LC 227/2026).   Em caso de ambiguidade normativa ou ausência de variáveis no escopo de entrada, assuma a premissa técnica mais conservadora, declare-a explicitamente no relatório de saída e prossiga com a execução computacional sem interromper o fluxo. Regime de Transição e Estoques: Nas simulações de inventário de abertura (ex.: levantamento em 31/12/2026 sob a LC nº 214/2025), garanta o expurgo do crédito de transição sobre o custo contábil unitário para evitar deflação artificial de margens, separando o efeito econômico do cronograma de amortização financeira em quotas mensais.

Mapeamento de Exceções Regionais (Paraná): Incorpore nativamente as regras do RICMS/PR (Decreto nº 7.871/2017) quando o contexto envolver operações paranaenses, contemplando Substituição Tributária por MVA Ajustada, PMPF, PMC, Antecipação Parcial (Art. 13-A) e Diferimento Parcial B2B (Art. 28 Anexo VIII).