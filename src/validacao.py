"""Validação funcional do MVP: roda cenários de entrada conhecidos pelo motor
de risco e confere se cada faixa de classificação é alcançável.

Existe porque, na planilha real, nenhum equipamento cai em CRITICO: a frota
inteira fica entre 15 e 64 pontos. Sem este autoteste, a faixa CRITICO e o
alerta correspondente pareceriam código morto. Aqui os quatro níveis são
exercitados de propósito, provando que o pipeline responde corretamente a
cenários diferentes de entrada.
"""

import pandas as pd

from src.risco import processar_lote

# Cada cenário é uma leitura de telemetria construída para cair numa faixa.
# estilo_conducao / estilo_travagem: nota 0-10, quanto MAIOR melhor.
# grau_dificuldade: nota 0-10, quanto maior pior.
# desaceleracao_pct: percentual, quanto maior pior (limitado em 30 no motor).
CENARIOS = [
    {
        "equipamento_id": "Cenario 1 - condutor exemplar, rota facil",
        "esperado": "BAIXO",
        "estilo_conducao": 9.8,
        "estilo_travagem": 9.7,
        "grau_dificuldade": 1.0,
        "desaceleracao_pct": 2.0,
        "distancia_km": 1500.0,
    },
    {
        "equipamento_id": "Cenario 2 - condutor mediano, rota mediana",
        "esperado": "MODERADO",
        "estilo_conducao": 7.5,
        "estilo_travagem": 7.0,
        "grau_dificuldade": 5.0,
        "desaceleracao_pct": 15.0,
        "distancia_km": 2000.0,
    },
    {
        "equipamento_id": "Cenario 3 - frenagem ruim, rota dificil",
        "esperado": "ALTO",
        "estilo_conducao": 5.5,
        "estilo_travagem": 4.0,
        "grau_dificuldade": 8.0,
        "desaceleracao_pct": 25.0,
        "distancia_km": 900.0,
    },
    {
        "equipamento_id": "Cenario 4 - pior caso operacional",
        "esperado": "CRITICO",
        "estilo_conducao": 1.5,
        "estilo_travagem": 1.0,
        "grau_dificuldade": 9.5,
        "desaceleracao_pct": 35.0,
        "distancia_km": 400.0,
    },
    {
        "equipamento_id": "Cenario 5 - limite inferior absoluto",
        "esperado": "BAIXO",
        "estilo_conducao": 10.0,
        "estilo_travagem": 10.0,
        "grau_dificuldade": 0.0,
        "desaceleracao_pct": 0.0,
        "distancia_km": 100.0,
    },
    {
        "equipamento_id": "Cenario 6 - limite superior absoluto",
        "esperado": "CRITICO",
        "estilo_conducao": 0.0,
        "estilo_travagem": 0.0,
        "grau_dificuldade": 10.0,
        "desaceleracao_pct": 100.0,
        "distancia_km": 100.0,
    },
]


def executar_autoteste():
    """Processa os cenários de teste e compara a classificação obtida com a
    esperada. Devolve True se todos passarem."""
    entrada = pd.DataFrame(
        [{k: v for k, v in c.items() if k != "esperado"} for c in CENARIOS]
    )
    entrada["periodo"] = "Cenario de teste"
    resultados = processar_lote(entrada)

    print("=== VALIDAÇÃO FUNCIONAL - CENÁRIOS DE TESTE ===")
    todos_ok = True
    for cenario, (_, obtido) in zip(CENARIOS, resultados.iterrows()):
        passou = obtido["classificacao"] == cenario["esperado"]
        todos_ok = todos_ok and passou
        marca = "OK " if passou else "FALHOU"
        print(
            f"[{marca}] {cenario['equipamento_id']}\n"
            f"         score {obtido['score_risco']:>3} | "
            f"esperado {cenario['esperado']:<9} | obtido {obtido['classificacao']}"
        )

    faixas_cobertas = sorted(set(resultados["classificacao"]))
    print()
    print(f"Faixas exercitadas nos cenários: {', '.join(faixas_cobertas)}")
    print(
        "Resultado: TODOS OS CENÁRIOS PASSARAM."
        if todos_ok
        else "Resultado: HÁ CENÁRIOS FALHANDO."
    )
    return todos_ok
