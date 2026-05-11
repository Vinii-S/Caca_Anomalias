"""
Módulo: seed_ctrl.py
Descrição: Popula o banco de dados com os dados históricos de treino
           (transacoes_treino.json) na primeira execução do sistema,
           aplicando as regras de detecção sobre todos os registros.
Autor: Squad 4
Data: 2026
"""

import os
import sqlite3
from datetime import time as time_obj

import pandas as pd

from models.database import SessionLocal
from models.transacao import Transacao


def popular_banco_se_vazio() -> None:
    """
    Importa os dados do JSON de treino caso o banco esteja vazio.
    Aplica as mesmas três regras de detecção do anomaly_ctrl sobre
    o histórico antes de persistir.
    """

    db = SessionLocal()
    total = db.query(Transacao).count()
    db.close()

    if total > 0:
        print(f"[seed] Banco já populado com {total} registros. Nenhuma ação necessária.")
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_json = os.path.join(base_dir, "data", "transacoes_treino.json")

    if not os.path.exists(caminho_json):
        print(f"[seed] Arquivo de dados não encontrado: {caminho_json}")
        return

    print(f"[seed] Importando dados de: {caminho_json}")
    df = pd.read_json(caminho_json)

    # Aplica as regras de detecção sobre o histórico
    df["hora_obj"] = pd.to_datetime(df["hora"], format="%H:%M", errors="coerce").dt.time
    media_por_conta = df.groupby("conta")["valor"].transform("mean")

    cond_hora       = ((df["hora_obj"] >= time_obj(22, 0)) | (df["hora_obj"] <= time_obj(5, 0))) & (df["valor"] > 500)
    cond_tentativas = df["tentativas"] >= 2
    cond_media      = df["valor"] > (media_por_conta * 3)

    df["verifica_fraude"] = cond_hora | cond_tentativas | cond_media
    df = df.drop(columns=["hora_obj"])

    conn = sqlite3.connect("transacoes_db.db")
    df.to_sql("transacoes", conn, if_exists="append", index=False)
    conn.close()

    print(f"[seed] {len(df)} transações importadas com sucesso.")
