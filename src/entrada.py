"""Entrada e validacao de dados de telemetria (planilha FleetBoard)."""

import pandas as pd

COLUNAS_ORIGEM = {
    "Veículo Anonimizado": "equipamento_id",
    "Origem_Mes": "periodo",
    "Estilo de condução (Pontuação)": "estilo_conducao",
    "Estilo de condução na travagem (Pontuação)": "estilo_travagem",
    "Grau de dificuldade (Pontuação)": "grau_dificuldade",
    "Desaceleração/total percorrido (%)": "desaceleracao_pct",
    "Total percorrido (km)": "distancia_km",
}

CAMPOS_OBRIGATORIOS = [
    "equipamento_id",
    "estilo_conducao",
    "estilo_travagem",
    "grau_dificuldade",
    "desaceleracao_pct",
]


def _numero_br_para_float(valor):
    """Converte string em formato brasileiro ('1.024,78') para float."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if texto == "" or texto.lower() == "nan":
        return None
    if "," in texto:
        # O ponto só é separador de milhar quando há vírgula decimal. Sem essa
        # checagem, um valor exportado noutro locale ("8.5") viraria 85 - erro
        # de 10x que passaria despercebido, já que o score seguiria válido.
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def carregar_planilha_fleetboard(caminho_arquivo, aba="Base Consolidada"):
    """Lê a planilha FleetBoard bruta e devolve um DataFrame com as colunas
    renomeadas para os nomes usados no motor de risco."""
    bruto = pd.read_excel(caminho_arquivo, sheet_name=aba)

    colunas_presentes = {k: v for k, v in COLUNAS_ORIGEM.items() if k in bruto.columns}
    df = bruto[list(colunas_presentes.keys())].rename(columns=colunas_presentes)

    campos_numericos = [
        "estilo_conducao",
        "estilo_travagem",
        "grau_dificuldade",
        "desaceleracao_pct",
        "distancia_km",
    ]
    for campo in campos_numericos:
        if campo in df.columns:
            df[campo] = df[campo].apply(_numero_br_para_float)

    return df


def validar_dados(df):
    """Separa registros validos de registros com campos obrigatorios
    ausentes ou inconsistentes. Devolve (df_validos, df_invalidos)."""
    df = df.copy()
    df["_erros"] = ""

    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in df.columns:
            df["_erros"] += f"coluna '{campo}' ausente na planilha; "
            continue
        faltando = df[campo].isna()
        df.loc[faltando, "_erros"] += f"{campo} ausente; "

    if "distancia_km" in df.columns:
        suspeito = df["distancia_km"].fillna(0) <= 0
        df.loc[suspeito, "_erros"] += "distancia_km inválida (<=0); "

    invalidos = df[df["_erros"] != ""].copy()
    validos = df[df["_erros"] == ""].drop(columns="_erros").reset_index(drop=True)
    invalidos = invalidos.reset_index(drop=True)

    return validos, invalidos
