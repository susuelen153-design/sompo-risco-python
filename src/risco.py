"""Motor de risco: calcula o score de vistoria, classifica e gera alertas.

Reaproveita o vocabulario e as faixas de valor ja validadas no schema do
banco SOMPO (Cognitive Data Science, Sprint 3): score 0-100 e classificacao
em BAIXO / MODERADO / ALTO / CRITICO.
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


NOMES_FATORES = {
    "estilo_conducao": "Estilo de conducao",
    "estilo_travagem": "Estilo de frenagem",
    "grau_dificuldade": "Dificuldade da rota",
    "desaceleracao_pct": "Desaceleracao/frenagem brusca",
}


def calcular_contribuicoes(estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct):
    """Calcula quantos pontos de risco cada indicador contribuiu, para
    permitir identificar o principal fator associado ao risco."""
    return {
        "estilo_conducao": (10 - estilo_conducao) * PESO_ESTILO_CONDUCAO,
        "estilo_travagem": (10 - estilo_travagem) * PESO_ESTILO_TRAVAGEM,
        "grau_dificuldade": grau_dificuldade * PESO_GRAU_DIFICULDADE,
        "desaceleracao_pct": desaceleracao_pct * PESO_DESACELERACAO,
    }


def calcular_score_risco(estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct):
    """Calcula o score de risco (0-100) a partir dos indicadores de
    telemetria de um equipamento."""
    contribuicoes = calcular_contribuicoes(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    score = sum(contribuicoes.values())
    score = max(0, min(100, score))
    return round(score)


def identificar_fator_principal(estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct):
    """Identifica qual indicador mais contribuiu para o score de risco."""
    contribuicoes = calcular_contribuicoes(
        estilo_conducao, estilo_travagem, grau_dificuldade, desaceleracao_pct
    )
    chave_principal = max(contribuicoes, key=contribuicoes.get)
    return NOMES_FATORES[chave_principal]


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
        return f"[ALERTA CRITICO] {equipamento_id}: risco {score} - inspecao imediata recomendada."
    if classificacao == "ALTO":
        return f"[ALERTA] {equipamento_id}: risco {score} - agendar inspecao em breve."
    if classificacao == "MODERADO":
        return f"[ATENCAO] {equipamento_id}: risco {score} - monitorar na proxima vistoria."
    return f"[OK] {equipamento_id}: risco {score} - dentro do esperado."


def processar_registro(registro):
    """Processa um unico registro de telemetria (dict ou pandas.Series) e
    devolve o resultado completo do motor de risco para ele."""
    score = calcular_score_risco(
        registro["estilo_conducao"],
        registro["estilo_travagem"],
        registro["grau_dificuldade"],
        registro["desaceleracao_pct"],
    )
    classificacao = classificar_risco(score)
    alerta = gerar_alerta(registro["equipamento_id"], score, classificacao)
    fator_principal = identificar_fator_principal(
        registro["estilo_conducao"],
        registro["estilo_travagem"],
        registro["grau_dificuldade"],
        registro["desaceleracao_pct"],
    )

    return {
        "equipamento_id": registro["equipamento_id"],
        "periodo": registro.get("periodo", "-"),
        "condicao_ambiente": registro.get("condicao_ambiente", "-"),
        "modo_operacao": registro.get("modo_operacao", "-"),
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
