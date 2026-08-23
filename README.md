# MVP de Análise de Risco Operacional

Disciplina: Computational Thinking with Python - Sprint 3
Professor: Kévin Allan Sales Rodrigues

# Objetivo

MVP em Python que recebe dados operacionais de equipamentos (telemetria real
ou simulada), processa essas informações num motor de risco e gera saídas
interpretáveis: score, classificação e alertas. É a primeira versão do
backend de análise de risco do projeto Sompo Seguros nessa disciplina,
conectando a entrada de dados ao modelo de risco.

# Relação com o resto do projeto

Reaproveitamos o vocabulário e as faixas de valor que já validamos em
outras entregas do grupo:

- Score 0-100 e classificação BAIXO / MODERADO / ALTO / CRITICO: mesma
  convenção usada no modelo físico de dados da disciplina Cognitive Data
  Science e do nosso mockup (`gemini_analyses`, `score_snapshots`, `equipment_profiles` no
  schema SOMPO).
- "Score de vistoria" e "perfil do equipamento": termos que vem do
  `CONTEXT.md` do repositório real do produto (`sompo-field-risk`, em
  TypeScript/Node). Esse MVP em Python é um exercício separado do
  repositório e implementa, de um jeito mais simples o
  eixo de contexto/telemetria do score de vistoria. Os eixos de condição
  física (fotos) e conformidade operacional (checklist) ficam com o motor
  de IA (Gemini) do produto real.

# Dados de entrada

Duas fontes, escolhidas por linha de comando:

1. `fleetboard` (padrão): planilha real de telemetria de frota
   (`data/Base_Consolidada_Anonimizada_testes_4585.xlsx`), com estilo de
   condução, frenagem, dificuldade de rota e desaceleração por
   veículo/mês. Representa equipamentos em `operation_mode = TRANSPORTE`.
2. `simulado`: leituras de sensor/API geradas artificialmente
   (`src/sensores.py`), pra simular um equipamento sem telemetria real
   disponível ainda.

# Regras de negócio implementadas

O score de risco (0-100) é calculado a partir de quatro indicadores de
telemetria, com pesos que definimos pra este MVP (ver `src/risco.py`):

| Indicador | Direção | Peso |
|---|---|---|
| Estilo de condução (nota 0-10, quanto maior melhor) | invertido | até 40 pontos |
| Estilo de condução na frenagem (nota 0-10, quanto maior melhor) | invertido | até 30 pontos |
| Grau de dificuldade da rota (nota 0-10) | direto | até 15 pontos |
| Desaceleração / total percorrido (%) | direto | até 15 pontos |

Classificação:

| Faixa | Classificação |
|---|---|
| 0-25 | BAIXO |
| 26-50 | MODERADO |
| 51-75 | ALTO |
| 76-100 | CRITICO |

Os pesos e as faixas de corte são uma definição nossa para este MVP. O
enunciado não fixa uma fórmula exata, só pede faixa 0-100 e classificações
interpretáveis. Dá pra ajustar em `src/risco.py`.

Cada resultado também mostra o fator principal que mais pesou no score
daquele equipamento (`identificar_fator_principal` em `src/risco.py`), e o
console imprime um ranking dos fatores mais frequentes na frota inteira
(seção `PRINCIPAIS FATORES DE RISCO NA FROTA`).

# Estrutura do projeto

```
sompo-risco-python/
├── main.py              # pipeline: entrada -> processamento -> saida
├── requirements.txt
├── data/
│   └── Base_Consolidada_Anonimizada_testes_4585.xlsx
├── output/               # gerado ao rodar (csv, json, grafico)
└── src/
    ├── entrada.py         # leitura da planilha + validacao de dados
    ├── sensores.py         # simulacao de sensores/API
    ├── risco.py             # calculo de score, classificacao e alertas
    └── saida.py              # resumo no console, exportacoes, grafico


# Como rodar

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Com a planilha real
python main.py --fonte fleetboard

# Com sensores simulados
python main.py --fonte simulado --quantidade 10

# Consulta rapida por equipamento (funciona com qualquer --fonte)
python main.py --fonte fleetboard --consultar "Teresa"
```

# Saídas geradas em `output/`

- `resultados.csv` / `resultados.json`: um registro por equipamento
  processado, com score, classificação e alerta.
- `distribuicao_risco.png`: gráfico de barras com a quantidade de
  equipamentos em cada faixa de risco.
- Resumo impresso no console (`=== RESULTADO ===`, `=== ALERTAS ===`,
  `=== DISTRIBUICAO POR CLASSIFICACAO ===`).

# Validação e tratamento de dados

`src/entrada.py` descarta registros com campos obrigatórios ausentes
(estilo de condução, frenagem, dificuldade, desaceleração) ou distância
percorrida inválida (<= 0), e avisa quantos registros foram descartados
antes de processar. Rodando com a planilha real, ele descarta 76 de 2092
registros por esse motivo.

# Requisitos técnicos atendidos

- Funções: todo o fluxo é modularizado em funções por responsabilidade
  (`entrada.py`, `sensores.py`, `risco.py`, `saida.py`).
- Estruturas condicionais: validação de campos obrigatórios
  (`validar_dados`), classificação por faixa (`classificar_risco`) e
  geração de alertas por nível (`gerar_alerta`).
- pandas: leitura da planilha, conversão de números em formato brasileiro,
  filtragem de registros inválidos e agregação da distribuição de risco.
- Pipeline claro: `main.py` separa entrada, processamento e saída em
  etapas sequenciais e legíveis.

# Limitações conhecidas / próximos passos

- O score cobre só o eixo de contexto/telemetria. Os eixos de condição
  física (fotos) e conformidade operacional (checklist) ficam pra quando
  integrarmos com o motor de IA do produto real.
- Os pesos da fórmula de risco são nossa primeira definição, não
  calibrada estatisticamente.
