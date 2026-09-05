"""Geracao de saidas: resumo no console, exportacoes e grafico simples."""

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def exibir_resumo(df_resultados):
    """Imprime um resumo legivel dos resultados processados."""
    print("=== RESULTADO ===")
    for _, linha in df_resultados.iterrows():
        print(f"{linha['equipamento_id']} -> {linha['classificacao']} ({linha['score_risco']})")

    print()
    print("=== ALERTAS ===")
    criticos_ou_altos = df_resultados[df_resultados["classificacao"].isin(["ALTO", "CRITICO"])]
    if criticos_ou_altos.empty:
        print("Nenhum equipamento em ALTO ou CRITICO nesta rodada.")
    else:
        for _, linha in criticos_ou_altos.iterrows():
            print(linha["alerta"])

    print()
    print("=== DISTRIBUIÇÃO POR CLASSIFICAÇÃO ===")
    contagem = df_resultados["classificacao"].value_counts()
    for rotulo in ["BAIXO", "MODERADO", "ALTO", "CRITICO"]:
        print(f"{rotulo}: {contagem.get(rotulo, 0)}")

    faixas_vazias = [r for r in ["BAIXO", "MODERADO", "ALTO", "CRITICO"] if contagem.get(r, 0) == 0]
    if faixas_vazias:
        print(
            f"(nenhum equipamento nas faixas {', '.join(faixas_vazias)} nesta rodada "
            "- ver leitura relativa abaixo)"
        )

    print()
    print("=== PRINCIPAIS FATORES DE RISCO NA FROTA ===")
    if "fator_principal" in df_resultados.columns:
        ranking = df_resultados["fator_principal"].value_counts()
        for fator, quantidade in ranking.items():
            print(f"{fator}: {quantidade} equipamento(s)")

    exibir_contexto_operacional(df_resultados)
    exibir_leitura_relativa(df_resultados)


def exibir_contexto_operacional(df_resultados):
    """Mostra o efeito dos agravantes de ambiente e modo de operacao.

    So aparece quando a fonte de dados traz esses campos. A planilha real da
    FleetBoard e de telemetria pura, entao nessa rodada os fatores ficam
    todos em 1,00 e a secao e omitida.
    """
    if "fator_ambiente" not in df_resultados.columns:
        return

    agravados = df_resultados[
        (df_resultados["fator_ambiente"] > 1) | (df_resultados["fator_operacao"] > 1)
    ]
    if agravados.empty:
        return

    print()
    print("=== AGRAVANTES DE CONTEXTO OPERACIONAL ===")
    for _, linha in agravados.iterrows():
        acrescimo = linha["score_risco"] - linha["score_base"]
        print(
            f"{linha['equipamento_id']} | {linha['condicao_ambiente']} / "
            f"{linha['modo_operacao']} | base {linha['score_base']} "
            f"-> {linha['score_risco']} (+{acrescimo})"
        )
    print(
        f"{len(agravados)} de {len(df_resultados)} equipamento(s) tiveram o score "
        "agravado pelo ambiente e/ou pelo modo de operacao."
    )


def exibir_leitura_relativa(df_resultados):
    """Mostra a distribuição do score dentro da própria frota.

    A classificação BAIXO/MODERADO/ALTO/CRITICO usa faixas absolutas fixas
    (0-100), mantidas iguais às do schema SOMPO para as disciplinas
    conversarem entre si. Como o score real se concentra numa faixa estreita,
    a contagem por classificação sozinha engana: quase todo mundo cai em
    MODERADO. Os percentis abaixo mostram quem está pior *em relação à frota*,
    que é a leitura útil para priorizar vistoria.
    """
    scores = df_resultados["score_risco"]
    if scores.empty:
        return

    print()
    print("=== LEITURA RELATIVA À FROTA (percentis do score) ===")
    print(f"mínimo: {scores.min()}  |  mediana: {scores.median():.0f}  |  máximo: {scores.max()}")
    print(f"média: {scores.mean():.1f}  |  desvio padrão: {scores.std():.1f}")
    for percentil in [25, 50, 75, 90]:
        print(f"P{percentil}: {scores.quantile(percentil / 100):.0f}")

    corte = scores.quantile(0.90)
    piores = df_resultados[scores >= corte]
    print(
        f"{len(piores)} equipamento(s) no decil mais arriscado da frota "
        f"(score >= {corte:.0f}) - candidatos naturais a vistoria prioritária."
    )


def consultar_equipamento(df_resultados, termo_busca):
    """Consulta rapida: filtra os resultados por parte do nome/id do
    equipamento (busca case-insensitive)."""
    encontrados = df_resultados[
        df_resultados["equipamento_id"]
        .astype(str)
        .str.contains(termo_busca, case=False, na=False)
    ]
    if encontrados.empty:
        print(f"Nenhum equipamento encontrado para '{termo_busca}'.")
        return encontrados

    print(f"=== CONSULTA: '{termo_busca}' ===")
    for _, linha in encontrados.iterrows():
        print(
            f"{linha['equipamento_id']} | {linha['periodo']} | "
            f"score {linha['score_risco']} | {linha['classificacao']} | "
            f"fator principal: {linha['fator_principal']}"
        )
    return encontrados


def exportar_csv(df_resultados, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    df_resultados.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


def exportar_json(df_resultados, caminho):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    registros = df_resultados.to_dict(orient="records")
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(registros, arquivo, ensure_ascii=False, indent=2)
    return caminho


def gerar_grafico_distribuicao(df_resultados, caminho):
    """Gera um grafico de barras simples com a distribuicao de risco."""
    os.makedirs(os.path.dirname(caminho), exist_ok=True)

    ordem = ["BAIXO", "MODERADO", "ALTO", "CRITICO"]
    cores = {"BAIXO": "#2f9e6e", "MODERADO": "#d9a441", "ALTO": "#d97b1f", "CRITICO": "#c62828"}
    contagem = df_resultados["classificacao"].value_counts().reindex(ordem, fill_value=0)

    figura, eixo = plt.subplots(figsize=(6, 4))
    eixo.bar(contagem.index, contagem.values, color=[cores[r] for r in ordem])
    eixo.set_title("Distribuição de risco por equipamento")
    eixo.set_ylabel("Quantidade de equipamentos")
    figura.tight_layout()
    figura.savefig(caminho)
    plt.close(figura)

    return caminho
