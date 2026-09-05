"""Motor de risco: calcula o score de vistoria, classifica e gera alertas.

Reaproveita o vocabulario e as faixas de valor ja validadas no schema do
banco SOMPO (Cognitive Data Science, Sprint 3): score 0-100 e classificação
em BAIXO / MODERADO / ALTO / CRITICO.

O score tem duas partes:

1. Score base (0-100), calculado a partir dos quatro indicadores de
   TELEMETRIA. É o que a planilha real da FleetBoard fornece.
2. Agravantes de CONTEXTO OPERACIONAL (condição do ambiente e modo de
   operação), aplicados como multiplicadores sobre o score base.

A separação existe porque a base real do projeto é de telemetria pura: ela
não traz ambiente nem modo de operação. Os agravantes são NEUTROS (fator
1,00) quando esses campos estão ausentes, então a rodada com os dados reais
produz exatamente o score base. Já as leituras de sensor/API simuladas
(src/sensores.py) trazem os dois campos, e é por esse caminho que o motor
demonstra o consumo de entradas dinâmicas de ambiente e operação.
"""

import pandas as pd

FAIXAS_CLASSIFICACAO = [
    (0, 25, "BAIXO"),
    (26, 50, "MODERADO"),
    (51, 75, "ALTO"),
    (76, 100, "CRITICO"),
]

# Pesos do eixo de contexto/telemetria do score de vistoria. FleetBoard usa
# escala 0-10 para estilo_conducao/estilo_travagem onde nota ALTA = conducao
# boa (por isso o risco usa (10 - nota)); grau_dificuldade e desaceleracao_pct
# ja crescem no mesmo sentido do risco.
PESO_ESTILO_CONDUCAO = 4.0
PESO_ESTILO_TRAVAGEM = 3.0
PESO_GRAU_DIFICULDADE = 1.5
PESO_DESACELERACAO = 0.5

# Teto do indicador de desaceleração. Os outros três indicadores são limitados
# pela própria escala (0-10), mas desaceleracao_pct é um percentual sem teto
# natural: na planilha real chega a 40%, o que renderia até 20 pontos e
# estouraria o orçamento de 100 pontos do score. Limitar em 30% mantém o teto
# documentado de 15 pontos (30 * 0.5) e a soma dos quatro pesos em 100.
TETO_DESACELERACAO_PCT = 30.0

# Agravantes de contexto operacional. Multiplicam o score base.
# 1,00 = neutro (não agrava). Valores definidos por nós para este MVP:
# quanto pior a aderência/visibilidade, maior o agravante.
FATORES_AMBIENTE = {
    "TEMPO BOM": 1.00,
    "VENTO FORTE": 1.05,
    "NEBLINA": 1.10,
    "CHUVA LEVE": 1.10,
    "CHUVA FORTE": 1.20,
}
FATOR_AMBIENTE_PADRAO = 1.00

# Operação em CAMPO agrava: terreno irregular, manobra em solo agrícola e
# ausência de via pavimentada. TRANSPORTE (rodovia) é a referência neutra —
# e é o modo que representa a base real da FleetBoard.
FATORES_OPERACAO = {
    "TRANSPORTE": 1.00,
    "CAMPO": 1.10,
}
FATOR_OPERACAO_PADRAO = 1.00

NOMES_FATORES = {
    "estilo_conducao": "Estilo de condução",
    "estilo_travagem": "Estilo de frenagem",
    "grau_dificuldade": "Dificuldade da rota",
    "desaceleracao_pct": "Desaceleração/frenagem brusca",
}

NOME_FATOR_AMBIENTE = "Condição do ambiente"
NOME_FATOR_OPERACAO = "Modo de operação"


def _normalizar_categoria(valor):
    """Normaliza um campo categórico vindo de sensor/planilha. Devolve None
    quando o campo está ausente, vazio ou preenchido com o marcador '-'."""
    if valor is None:
        return None
    if isinstance(valor, float) and pd.isna(valor):
        return None
    texto = str(valor).strip()
    if texto == "" or texto == "-" or texto.lower() == "nan":
        return None
    return texto.upper()


def obter_fator_ambiente(condicao_ambiente):
    """Fator de agravamento da condição do ambiente (1,00 = neutro)."""
    chave = _normalizar_categoria(condicao_ambiente)
    if chave is None:
        return FATOR_AMBIENTE_PADRAO
    return FATORES_AMBIENTE.get(chave, FATOR_AMBIENTE_PADRAO)


def obter_fator_operacao(modo_operacao):
    """Fator de agravamento do modo de operação (1,00 = neutro)."""
    chave = _normalizar_categoria(modo_operacao)
    if chave is None:
        return FATOR_OPERACAO_PADRAO
    return FATORES_OPERACAO.get(chave, FATOR_OPERACAO_PADRAO)


def calcular_contribuicoes(estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct):
    """Calcula quantos pontos de risco cada indicador de telemetria
    contribuiu, para permitir identificar o principal fator do risco."""
    desaceleracao_limitada = min(desaceleracao_pct, TETO_DESACELERACAO_PCT)
    return {
        "estilo_conducao": (10 - estilo_conducao) * PESO_ESTILO_CONDUCAO,
        "estilo_travagem": (10 - estilo_travagem) * PESO_ESTILO_TRAVAGEM,
        "grau_dificuldade": grau_dificuldade * PESO_GRAU_DIFICULDADE,
        "desaceleracao_pct": desaceleracao_limitada * PESO_DESACELERACAO,
    }


def calcular_score_base(estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct):
    """Score de risco (0-100) só com os indicadores de telemetria."""
    contribuicoes = calcular_contribuicoes(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    return max(0.0, min(100.0, sum(contribuicoes.values())))


def calcular_score_risco(
    estilo_conducao,
    estilo_travagem,
    grau_dificuldade,
    desaceleracao_pct,
    condicao_ambiente=None,
    modo_operacao=None,
):
    """Score de risco final (0-100): telemetria agravada pelo contexto
    operacional. Sem ambiente/operação, devolve o próprio score base."""
    base = calcular_score_base(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    agravado = base * obter_fator_ambiente(condicao_ambiente) * obter_fator_operacao(modo_operacao)
    return round(max(0.0, min(100.0, agravado)))


def identificar_fator_principal(
    estilo_conducao,
    estilo_travagem,
    grau_dificuldade,
    desaceleracao_pct,
    condicao_ambiente=None,
    modo_operacao=None,
):
    """Identifica o que mais pesou no score: o indicador de telemetria de
    maior contribuição ou, se agravar mais que ele, o contexto operacional."""
    contribuicoes = calcular_contribuicoes(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    chave_principal = max(contribuicoes, key=contribuicoes.get)
    candidatos = {NOMES_FATORES[chave_principal]: contribuicoes[chave_principal]}

    base = calcular_score_base(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    fator_ambiente = obter_fator_ambiente(condicao_ambiente)
    fator_operacao = obter_fator_operacao(modo_operacao)
    # Pontos que cada agravante acrescentou sobre o score base.
    candidatos[NOME_FATOR_AMBIENTE] = base * (fator_ambiente - 1)
    candidatos[NOME_FATOR_OPERACAO] = base * fator_ambiente * (fator_operacao - 1)

    return max(candidatos, key=candidatos.get)


def classificar_risco(score):
    """Classifica o score numerico em BAIXO / MODERADO / ALTO / CRITICO."""
    for minimo, maximo, rotulo in FAIXAS_CLASSIFICACAO:
        if minimo <= score <= maximo:
            return rotulo
    return "INDEFINIDO"


def gerar_alerta(equipamento_id, score, classificacao):
    """Gera uma mensagem de alerta compreensivel para o usuario final,
    de acordo com o nivel de risco identificado."""
    if classificacao == "CRITICO":
        return f"[ALERTA CRITICO] {equipamento_id}: risco {score} - inspeção imediata recomendada."
    if classificacao == "ALTO":
        return f"[ALERTA] {equipamento_id}: risco {score} - agendar inspeção em breve."
    if classificacao == "MODERADO":
        return f"[ATENÇÃO] {equipamento_id}: risco {score} - monitorar na próxima vistoria."
    return f"[OK] {equipamento_id}: risco {score} - dentro do esperado."


def processar_registro(registro):
    """Processa um unico registro de telemetria (dict ou pandas.Series) e
    devolve o resultado completo do motor de risco para ele."""
    condicao_ambiente = registro.get("condicao_ambiente")
    modo_operacao = registro.get("modo_operacao")

    base = calcular_score_base(
        registro["estilo_conducao"],
        registro["estilo_travagem"],
        registro["grau_dificuldade"],
        registro["desaceleracao_pct"],
    )
    fator_ambiente = obter_fator_ambiente(condicao_ambiente)
    fator_operacao = obter_fator_operacao(modo_operacao)

    score = calcular_score_risco(
        registro["estilo_conducao"],
        registro["estilo_travagem"],
        registro["grau_dificuldade"],
        registro["desaceleracao_pct"],
        condicao_ambiente,
        modo_operacao,
    )
    classificacao = classificar_risco(score)
    alerta = gerar_alerta(registro["equipamento_id"], score, classificacao)
    fator_principal = identificar_fator_principal(
        registro["estilo_conducao"],
        registro["estilo_travagem"],
        registro["grau_dificuldade"],
        registro["desaceleracao_pct"],
        condicao_ambiente,
        modo_operacao,
    )

    return {
        "equipamento_id": registro["equipamento_id"],
        "periodo": registro.get("periodo", "-"),
        "condicao_ambiente": condicao_ambiente if _normalizar_categoria(condicao_ambiente) else "-",
        "modo_operacao": modo_operacao if _normalizar_categoria(modo_operacao) else "-",
        "score_base": round(base),
        "fator_ambiente": round(fator_ambiente, 2),
        "fator_operacao": round(fator_operacao, 2),
        "score_risco": score,
        "classificacao": classificacao,
        "fator_principal": fator_principal,
        "alerta": alerta,
    }


def processar_lote(df):
    """Aplica o motor de risco a todos os registros de um DataFrame de
    telemetria e devolve um DataFrame com os resultados."""
    resultados = [processar_registro(linha) for _, linha in df.iterrows()]
    return pd.DataFrame(resultados)
