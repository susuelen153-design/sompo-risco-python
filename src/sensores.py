"""Simulacao de leitura de sensores/API, para rodar o motor de risco sem
depender da planilha real (ex.: equipamento novo, ainda sem telemetria)."""

import random

import pandas as pd

NOMES_EQUIPAMENTO_DEMO = [
    "Trator Demo 1",
    "Trator Demo 2",
    "Colheitadeira Demo 1",
    "Caminhao Demo 1",
    "Caminhao Demo 2",
]

CONDICOES_AMBIENTE = ["Tempo bom", "Chuva leve", "Chuva forte", "Neblina", "Vento forte"]
MODOS_OPERACAO = ["CAMPO", "TRANSPORTE"]


def simular_leitura_sensor(equipamento_id):
    """Gera uma leitura simulada de sensor/API pra um equipamento, como se
    viesse de telemetria em tempo real: dados de condução (telemetria),
    condicao ambiente e modo de operacao."""
    return {
        "equipamento_id": equipamento_id,
        "periodo": "Simulado",
        "estilo_conducao": round(random.uniform(2.0, 9.5), 2),
        "estilo_travagem": round(random.uniform(2.0, 9.5), 2),
        "grau_dificuldade": round(random.uniform(1.0, 9.0), 2),
        "desaceleracao_pct": round(random.uniform(0.0, 25.0), 2),
        "distancia_km": round(random.uniform(50.0, 3000.0), 1),
        "condicao_ambiente": random.choice(CONDICOES_AMBIENTE),
        "modo_operacao": random.choice(MODOS_OPERACAO),
    }


def simular_lote(quantidade=5):
    """Simula um lote de leituras de sensores para varios equipamentos."""
    nomes = (NOMES_EQUIPAMENTO_DEMO * ((quantidade // len(NOMES_EQUIPAMENTO_DEMO)) + 1))[:quantidade]
    leituras = [simular_leitura_sensor(nome) for nome in nomes]
    return pd.DataFrame(leituras)
