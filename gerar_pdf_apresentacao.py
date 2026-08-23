# -*- coding: utf-8 -*-
"""Gera um PDF de apresentacao do MVP, com resumo, regras de negocio,
resultados da rodada com dados reais e o grafico de distribuicao."""

import os

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak,
    KeepTogether,
)

DIR_BASE = os.path.dirname(os.path.abspath(__file__))
DIR_SAIDA = os.path.join(DIR_BASE, "output")
CAMINHO_PDF = os.path.join(DIR_BASE, "apresentacao_sompo_risco_python.pdf")

AZUL = colors.HexColor("#1f3a5f")
CINZA = colors.HexColor("#555555")
FUNDO_TABELA = colors.HexColor("#eef1f6")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloCapa", fontSize=20, leading=24, textColor=AZUL, spaceAfter=6))
styles.add(ParagraphStyle(name="Subtitulo", fontSize=11, leading=15, textColor=CINZA, spaceAfter=2))
styles.add(ParagraphStyle(name="H2", fontSize=14, leading=18, textColor=AZUL, spaceBefore=14, spaceAfter=8))
styles.add(ParagraphStyle(name="Corpo", fontSize=10, leading=15, spaceAfter=8))
styles.add(ParagraphStyle(name="Link", fontSize=10, leading=15, textColor=colors.HexColor("#0b5fa5")))


def tabela_padrao(dados, larguras=None):
    t = Table(dados, colWidths=larguras)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO_TABELA]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def montar_pdf():
    df = pd.read_csv(os.path.join(DIR_SAIDA, "resultados.csv"), encoding="utf-8")

    doc = SimpleDocTemplate(
        CAMINHO_PDF, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    story = []

    # Capa
    story.append(Paragraph("Sompo Field Risk", styles["TituloCapa"]))
    story.append(Paragraph("MVP de Análise de Risco Operacional (Python)", styles["Subtitulo"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Disciplina: Computational Thinking with Python - Sprint 3", styles["Corpo"]))
    story.append(Paragraph("Professor: Kévin Allan Sales Rodrigues", styles["Corpo"]))
    story.append(Paragraph("Projeto: Sompo Seguros", styles["Corpo"]))
    story.append(Spacer(1, 14))

    # Objetivo
    story.append(Paragraph("Objetivo", styles["H2"]))
    story.append(Paragraph(
        "MVP em Python que recebe dados operacionais de equipamentos (telemetria real ou "
        "simulada), processa essas informações num motor de risco e gera saídas "
        "interpretáveis: score, classificação e alertas. É a primeira versão do backend de "
        "análise de risco do projeto Sompo Seguros nessa disciplina, conectando a entrada "
        "de dados ao modelo de risco.", styles["Corpo"],
    ))

    # Arquitetura
    story.append(Paragraph("Estrutura do projeto", styles["H2"]))
    story.append(tabela_padrao([
        ["Arquivo", "Responsabilidade"],
        ["main.py", "Pipeline: entrada -> processamento -> saída"],
        ["src/entrada.py", "Leitura da planilha e validação de dados obrigatórios"],
        ["src/sensores.py", "Simulação de sensores/API (telemetria, ambiente, operação)"],
        ["src/risco.py", "Cálculo do score, classificação, fator principal e alertas"],
        ["src/saida.py", "Resumo no console, exportações (CSV/JSON) e gráfico"],
    ], larguras=[5 * cm, 11 * cm]))

    # Regras de negocio
    story.append(PageBreak())
    story.append(Paragraph("Regras de negócio implementadas", styles["H2"]))
    story.append(Paragraph(
        "O score de risco (0-100) é calculado a partir de quatro indicadores de "
        "telemetria, com pesos definidos para este MVP:", styles["Corpo"],
    ))
    story.append(tabela_padrao([
        ["Indicador", "Direção", "Peso máximo"],
        ["Estilo de condução (nota 0-10)", "invertido", "40 pontos"],
        ["Estilo de condução na frenagem (nota 0-10)", "invertido", "30 pontos"],
        ["Grau de dificuldade da rota (nota 0-10)", "direto", "15 pontos"],
        ["Desaceleração / total percorrido (%)", "direto", "~15 pontos"],
    ], larguras=[9 * cm, 3.5 * cm, 3.5 * cm]))
    story.append(Spacer(1, 8))
    story.append(tabela_padrao([
        ["Faixa de score", "Classificação"],
        ["0 - 25", "BAIXO"],
        ["26 - 50", "MODERADO"],
        ["51 - 75", "ALTO"],
        ["76 - 100", "CRITICO"],
    ], larguras=[8 * cm, 8 * cm]))

    story.append(PageBreak())

    # Resultados
    story.append(Paragraph("Resultados - rodada com dados reais (FleetBoard)", styles["H2"]))
    total = len(df)
    contagem = df["classificacao"].value_counts()
    story.append(Paragraph(f"Total de equipamentos processados: {total}", styles["Corpo"]))
    story.append(tabela_padrao([
        ["Classificação", "Quantidade", "% da frota"],
        *[
            [rotulo, str(contagem.get(rotulo, 0)), f"{contagem.get(rotulo, 0) / total * 100:.1f}%"]
            for rotulo in ["BAIXO", "MODERADO", "ALTO", "CRITICO"]
        ],
    ], larguras=[6 * cm, 5 * cm, 5 * cm]))

    story.append(Spacer(1, 10))
    caminho_grafico = os.path.join(DIR_SAIDA, "distribuicao_risco.png")
    if os.path.exists(caminho_grafico):
        story.append(Image(caminho_grafico, width=11 * cm, height=7.4 * cm))

    story.append(Paragraph("Principais fatores de risco na frota", styles["H2"]))
    ranking = df["fator_principal"].value_counts()
    story.append(tabela_padrao(
        [["Fator", "Equipamentos onde foi o principal fator"]]
        + [[fator, str(qtd)] for fator, qtd in ranking.items()],
        larguras=[9 * cm, 7 * cm],
    ))

    top6 = df.sort_values("score_risco", ascending=False).head(6)
    linhas_top = [["Equipamento", "Período", "Score", "Classificação", "Fator principal"]]
    for _, linha in top6.iterrows():
        linhas_top.append([
            linha["equipamento_id"], linha["periodo"], str(linha["score_risco"]),
            linha["classificacao"], linha["fator_principal"],
        ])
    story.append(KeepTogether([
        Spacer(1, 10),
        Paragraph("Equipamentos com maior risco identificado", styles["H2"]),
        tabela_padrao(linhas_top, larguras=[4 * cm, 2.7 * cm, 1.8 * cm, 3 * cm, 4.5 * cm]),
    ]))

    # Requisitos tecnicos
    story.append(Spacer(1, 12))
    story.append(Paragraph("Requisitos técnicos atendidos", styles["H2"]))
    story.append(tabela_padrao([
        ["Requisito", "Onde está"],
        ["Funções para modularizar o fluxo", "entrada.py, sensores.py, risco.py, saida.py"],
        ["Estruturas condicionais (validação, classificação, alertas)", "validar_dados, classificar_risco, gerar_alerta"],
        ["Uso de pandas", "Leitura, limpeza e agregação dos dados"],
        ["Pipeline claro (entrada / processamento / saída)", "main.py"],
        ["README detalhado no GitHub", "Ver link do repositório abaixo"],
    ], larguras=[9 * cm, 7 * cm]))

    story.append(Paragraph("Cobertura funcional do enunciado", styles["H2"]))
    story.append(tabela_padrao([
        ["Item pedido", "Status"],
        ["Backend modular com funções", "OK"],
        ["Integração com o modelo de risco", "OK"],
        ["Entrada e validação de dados (reais ou simulados)", "OK"],
        ["Simulação de sensores/API (telemetria, ambiente, operação)", "OK"],
        ["Saídas interpretáveis (score, classificação, alertas)", "OK"],
        ["Relatórios/dashboards simples e fatores de risco", "OK"],
        ["Consulta rápida dos resultados", "OK"],
        ["Validação funcional do MVP (testado end-to-end)", "OK"],
    ], larguras=[11 * cm, 5 * cm]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Código-fonte", styles["H2"]))
    story.append(Paragraph(
        'Repositório (privado - acesso mediante convite): '
        '<link href="https://github.com/susuelen153-design/sompo-risco-python">'
        'github.com/susuelen153-design/sompo-risco-python</link>',
        styles["Link"],
    ))

    doc.build(story)
    print("PDF gerado em:", CAMINHO_PDF)


if __name__ == "__main__":
    montar_pdf()
