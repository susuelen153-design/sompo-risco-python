# Sompo Field Risk - MVP de Análise de Risco Operacional (Python)

Disciplina: Computational Thinking with Python — Sprint 3
Professor: Kévin Allan Sales Rodrigues

## Objetivo

MVP em Python que recebe dados operacionais de equipamentos (telemetria real ou
simulada), processa essas informações através de um motor de risco e gera
saídas interpretáveis (score, classificação e alertas). É a implementação
inicial do backend de análise de risco do projeto Sompo Seguros nesta
disciplina, conectando a entrada de dados ao modelo de risco.

## Relação com o restante do projeto

Este MVP reaproveita deliberadamente o vocabulário e as faixas de valor já
validadas em outras entregas do grupo:

- **Score 0–100** e classificação **BAIXO / MODERADO / ALTO / CRITICO** —
  mesma convenção usada no modelo físico de dados da disciplina Cognitive
  Data Science (`gemini_analyses`, `score_snapshots`, `equipment_profiles`
  no schema SOMPO).
- **"Score de vistoria"** e **"perfil do equipamento"** — termos definidos em
  `CONTEXT.md` do repositório real do produto (`sompo-field-risk`, stack
  TypeScript/Node). Este MVP em Python é um exercício acadêmico separado
  daquele repositório (que não é Python) e implementa, de forma simplificada
  e determinística, o eixo de **contexto/telemetria** do score de vistoria —
  os eixos de condição física (visão computacional) e conformidade
  operacional (checklist) pertencem ao motor de IA (Gemini) do produto real
  e estão fora do escopo desta atividade.

## Dados de entrada

Duas fontes possíveis, escolhidas via linha de comando:

1. **`fleetboard`** (padrão) — planilha real de telemetria de frota
   (`data/Base_Consolidada_Anonimizada_testes_4585.xlsx`), com indicadores de
   estilo de condução, frenagem, dificuldade de rota e desaceleração por
   veículo/mês. Representa equipamentos em `operation_mode = TRANSPORTE`.
2. **`simulado`** — leituras de sensor/API geradas artificialmente
   (`src/sensores.py`), simulando o caso de um equipamento sem telemetria
   real disponível ainda.

## Regras de negócio implementadas

O score de risco (0–100) é calculado a partir de quatro indicadores de
telemetria, com pesos definidos pelo grupo (ver `src/risco.py`):

| Indicador | Direção | Peso |
|---|---|---|
| Estilo de condução (nota 0–10, quanto maior melhor) | invertido | até 40 pontos |
| Estilo de condução na frenagem (nota 0–10, quanto maior melhor) | invertido | até 30 pontos |
| Grau de dificuldade da rota (nota 0–10) | direto | até 15 pontos |
| Desaceleração / total percorrido (%) | direto | até ~15 pontos |

Classificação:

| Faixa | Classificação |
|---|---|
| 0–25 | BAIXO |
| 26–50 | MODERADO |
| 51–75 | ALTO |
| 76–100 | CRITICO |

Os pesos e as faixas de corte são uma definição do grupo para este MVP — o
enunciado da disciplina não fixa uma fórmula exata, só pede faixa 0–100 e
classificações interpretáveis. Ajustar em `src/risco.py` caso o grupo
valide outros pesos com dados reais.

Cada resultado também identifica o **fator principal** que mais contribuiu
para o score daquele equipamento (`identificar_fator_principal` em
`src/risco.py`), e o console mostra um ranking de fatores mais frequentes
na frota inteira (seção `PRINCIPAIS FATORES DE RISCO NA FROTA`).

## Estrutura do projeto

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
```

## Como rodar

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

### Saídas geradas em `output/`

- `resultados.csv` / `resultados.json` — um registro por equipamento
  processado, com score, classificação e alerta.
- `distribuicao_risco.png` — gráfico de barras com a quantidade de
  equipamentos em cada faixa de risco.
- Resumo impresso no console (`=== RESULTADO ===`, `=== ALERTAS ===`,
  `=== DISTRIBUICAO POR CLASSIFICACAO ===`).

## Validação e tratamento de dados

`src/entrada.py` descarta registros com campos obrigatórios ausentes
(estilo de condução, frenagem, dificuldade, desaceleração) ou distância
percorrida inválida (`<= 0`), reportando quantos registros foram
descartados antes do processamento — a rodada com a planilha real descarta
76 de 2092 registros por esse motivo.

## Requisitos técnicos atendidos

- **Funções**: todo o fluxo é modularizado em funções puras por
  responsabilidade (`entrada.py`, `sensores.py`, `risco.py`, `saida.py`).
- **Estruturas condicionais**: validação de campos obrigatórios
  (`validar_dados`), classificação por faixa (`classificar_risco`) e
  geração de alertas por nível (`gerar_alerta`).
- **pandas**: leitura da planilha, limpeza/conversão de números em formato
  brasileiro, filtragem de registros inválidos e agregação da distribuição
  de risco.
- **Pipeline claro**: `main.py` separa entrada, processamento e saída em
  etapas sequenciais e legíveis.

## Limitações conhecidas / próximos passos

- O score cobre apenas o eixo de contexto/telemetria; os eixos de condição
  física (fotos) e conformidade operacional (checklist) ficam para quando o
  grupo integrar com o motor de IA do produto real.
- Os pesos da fórmula de risco são uma primeira definição do grupo, não
  calibrada estatisticamente — candidato natural para a disciplina de
  Machine Learning & Modelling (Sprint 3), que já pede ao menos 2 modelos
  treinados e validados sobre um dataset de risco.
