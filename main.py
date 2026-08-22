"""Ponto de entrada do MVP: Sompo Field Risk - Analise de Risco Operacional.

Pipeline: entrada -> processamento -> saida.
"""

import argparse
import os

from src.entrada import carregar_planilha_fleetboard, validar_dados
from src.sensores import simular_lote
from src.risco import processar_lote
from src.saida import (
    consultar_equipamento,
    exibir_resumo,
    exportar_csv,
    exportar_json,
    gerar_grafico_distribuicao,
)

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
DIR_SAIDA = os.path.join(DIR_BASE, "output")


def obter_dados_entrada(fonte, caminho_planilha, quantidade_simulada):
    if fonte == "fleetboard":
        bruto = carregar_planilha_fleetboard(caminho_planilha)
        validos, invalidos = validar_dados(bruto)
        if not invalidos.empty:
            print(f"[VALIDACAO] {len(invalidos)} registro(s) descartado(s) por dados incompletos/invalidos.")
        print(f"[ENTRADA] {len(validos)} registro(s) validos carregados de '{caminho_planilha}'.")
        return validos

    dados_simulados = simular_lote(quantidade_simulada)
    print(f"[ENTRADA] {len(dados_simulados)} leitura(s) de sensor simulada(s).")
    return dados_simulados


def main():
    parser = argparse.ArgumentParser(description="Sompo Field Risk - MVP de analise de risco operacional")
    parser.add_argument(
        "--fonte",
        choices=["fleetboard", "simulado"],
        default="fleetboard",
        help="Origem dos dados de entrada (planilha real ou sensores simulados).",
    )
    parser.add_argument(
        "--arquivo",
        default=os.path.join(DIR_BASE, "data", "Base_Consolidada_Anonimizada_testes_4585.xlsx"),
        help="Caminho da planilha FleetBoard (usado quando --fonte=fleetboard).",
    )
    parser.add_argument(
        "--quantidade",
        type=int,
        default=5,
        help="Quantidade de leituras simuladas (usado quando --fonte=simulado).",
    )
    parser.add_argument(
        "--consultar",
        default=None,
        help="Busca rapida por nome/id de equipamento nos resultados processados.",
    )
    argumentos = parser.parse_args()

    dados = obter_dados_entrada(argumentos.fonte, argumentos.arquivo, argumentos.quantidade)
    if dados.empty:
        print("Nenhum dado valido para processar. Encerrando.")
        return

    resultados = processar_lote(dados)
    exibir_resumo(resultados)

    if argumentos.consultar:
        print()
        consultar_equipamento(resultados, argumentos.consultar)

    caminho_csv = exportar_csv(resultados, os.path.join(DIR_SAIDA, "resultados.csv"))
    caminho_json = exportar_json(resultados, os.path.join(DIR_SAIDA, "resultados.json"))
    caminho_grafico = gerar_grafico_distribuicao(resultados, os.path.join(DIR_SAIDA, "distribuicao_risco.png"))

    print()
    print("=== ARQUIVOS GERADOS ===")
    print(caminho_csv)
    print(caminho_json)
    print(caminho_grafico)


if __name__ == "__main__":
    main()
