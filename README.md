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
| Desaceleração / total percorrido (%) | direto | até 15 pontos (`min(pct; 30) × 0,5`) |

Os três primeiros indicadores são limitados pela própria escala (0–10), mas a desaceleração é um
percentual **sem teto natural** — na planilha real chega a 40%, o que renderia 20 pontos e estouraria
o orçamento de 100. Por isso o motor limita o indicador em 30% (`TETO_DESACELERACAO_PCT` em
`src/risco.py`), mantendo os quatro pesos somando exatamente 100.

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
├── data/                 # nao versionado - ver aviso acima
│   └── Base_Consolidada_Anonimizada_testes_4585.xlsx
├── output/               # gerado ao rodar (csv, json, grafico)
└── src/
    ├── entrada.py         # leitura da planilha + validacao de dados
    ├── sensores.py         # simulacao de sensores/API
    ├── risco.py             # calculo de score, classificacao e alertas
    ├── validacao.py          # cenarios de teste do motor de risco
    └── saida.py               # resumo no console, exportacoes, grafico
```

> **A planilha de telemetria não está neste repositório.** Ela contém dados
> operacionais de frota e fica fora do versionamento (`data/` está no
> `.gitignore`). Para rodar com os dados reais, peça o arquivo ao grupo e
> salve em `data/Base_Consolidada_Anonimizada_testes_4585.xlsx`.
>
> **Sem a planilha o projeto roda mesmo assim:** `--fonte simulado` gera
> telemetria sintética e `--autoteste` valida o motor de risco. Os resultados
> da rodada com os dados reais estão registrados em `output/` e resumidos na
> seção *Resultados com os dados reais* abaixo.

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

# Validação funcional: roda os cenários de teste do motor de risco
python main.py --autoteste
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

# Resultados com os dados reais (FleetBoard)

Rodada com os **2016 registros válidos** (de 2092 brutos):

| Classificação | Equipamentos | % da frota |
|---|---|---|
| BAIXO | 101 | 5,0% |
| MODERADO | 1512 | 75,0% |
| ALTO | 403 | 20,0% |
| CRITICO | 0 | 0,0% |

| Fator principal | Equipamentos |
|---|---|
| Estilo de condução | 905 |
| Desaceleração / frenagem brusca | 595 |
| Dificuldade da rota | 485 |
| Estilo de frenagem | 31 |

## Por que nenhum equipamento aparece como CRITICO

O score real da frota se concentra entre **15 e 64 pontos** (média 41,3;
desvio 10,0). A faixa CRITICO (76-100) exige os quatro indicadores
simultaneamente ruins, o que não ocorre em nenhum registro do período.

Isso é um resultado, não um defeito — mas significa que **a contagem por
classificação sozinha engana**: 75% da frota em MODERADO diz mais sobre a
compressão da escala do que sobre a operação. Por isso o console também
imprime uma leitura relativa à frota, com os percentis do score e o recorte
do decil mais arriscado, que é a informação útil para priorizar vistoria:

```
P25: 34  |  P50: 41  |  P75: 48  |  P90: 56
214 equipamento(s) no decil mais arriscado da frota (score >= 56)
```

As faixas absolutas foram mantidas em 0-25 / 26-50 / 51-75 / 76-100 de
propósito, para continuarem compatíveis com a convenção do schema SOMPO
usado nas outras disciplinas do projeto.

# Validação funcional do MVP

`python main.py --autoteste` roda seis cenários de entrada construídos para
exercitar **todas** as faixas de classificação, incluindo as que não aparecem
nos dados reais:

```
[OK ] Cenario 1 - condutor exemplar, rota facil      score   4 | BAIXO
[OK ] Cenario 2 - condutor mediano, rota mediana     score  34 | MODERADO
[OK ] Cenario 3 - frenagem ruim, rota dificil        score  60 | ALTO
[OK ] Cenario 4 - pior caso operacional              score  90 | CRITICO
[OK ] Cenario 5 - limite inferior absoluto           score   0 | BAIXO
[OK ] Cenario 6 - limite superior absoluto           score 100 | CRITICO

Faixas exercitadas nos cenários: ALTO, BAIXO, CRITICO, MODERADO
Resultado: TODOS OS CENÁRIOS PASSARAM.
```

Os cenários 5 e 6 confirmam que a escala usa os extremos corretos: entrada
perfeita gera score 0, pior entrada possível gera score 100. Isso prova que a
lógica de CRITICO e o alerta correspondente funcionam, mesmo não sendo
acionados pela planilha atual.

# Requisitos técnicos atendidos

- Funções: todo o fluxo é modularizado em funções por responsabilidade
  (`entrada.py`, `sensores.py`, `risco.py`, `validacao.py`, `saida.py`).
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
