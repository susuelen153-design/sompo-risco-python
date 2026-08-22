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
    print("=== DISTRIBUICAO POR CLASSIFICACAO ===")
    contagem = df_resultados["classificacao"].value_counts()
    for rotulo in ["BAIXO", "MODERADO", "ALTO", "CRITICO"]:
        print(f"{rotulo}: {contagem.get(rotulo, 0)}")


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
    eixo.set_title("Distribuicao de risco por equipamento")
    eixo.set_ylabel("Quantidade de equipamentos")
    figura.tight_layout()
    figura.savefig(caminho)
    plt.close(figura)

    return caminho
