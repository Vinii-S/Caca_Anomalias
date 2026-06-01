"""
Módulo: repositories/data_repository.py
Descrição: Camada de acesso a dados. Concentra todas as operações de
           leitura e escrita no banco (queries SQLAlchemy e seed inicial).
           Não contém lógica de negócio — apenas persistence/queries.
Autor: Squad 4
Data: 2026
"""

import os
import sqlite3
from typing import Optional

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.config import JSON_TREINO, REGRAS_PADRAO
from models.models import Anomalia, RegraFraude, Transacao, TransacaoRegra


# ---------------------------------------------------------------------------
# Transações
# ---------------------------------------------------------------------------

def db_criar_transacao(db: Session, dados: dict) -> Transacao:
    """Persiste uma nova transação no banco."""
    transacao = Transacao(**dados)
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    return transacao


def db_buscar_transacao_por_id(db: Session, transaction_id: int) -> Transacao:
    """Busca transação pelo ID ou lança HTTP 404."""
    transacao = db.query(Transacao).filter(
        Transacao.id_transacao == transaction_id
    ).first()

    if not transacao:
        raise HTTPException(status_code=404, detail=f"Transação {transaction_id} não encontrada")
    return transacao


def db_listar_transacoes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    conta: Optional[str] = None,
    cidade: Optional[str] = None,
    tipo_transacao: Optional[str] = None,
    valor_minimo: Optional[float] = None,
    valor_maximo: Optional[float] = None,
    is_fraude: Optional[bool] = None,
) -> list[Transacao]:
    """Lista transações com filtros opcionais (RN09, RN10, RN11)."""
    query = db.query(Transacao)

    if categoria:
        query = query.filter(Transacao.categoria == categoria)
    if conta:
        query = query.filter(Transacao.conta == conta)
    if cidade:
        query = query.filter(Transacao.cidade == cidade)
    if tipo_transacao:
        query = query.filter(Transacao.tipo_transacao == tipo_transacao)
    if valor_minimo is not None:
        query = query.filter(Transacao.valor >= valor_minimo)
    if valor_maximo is not None:
        query = query.filter(Transacao.valor <= valor_maximo)
    if is_fraude is not None:
        query = query.filter(Transacao.is_fraude == is_fraude)

    return query.offset(skip).limit(limit).all()


def db_excluir_transacao(db: Session, transaction_id: int) -> dict:
    """Remove transação pelo ID ou lança HTTP 404."""
    transacao = db.query(Transacao).filter(
        Transacao.id_transacao == transaction_id
    ).first()

    if not transacao:
        raise HTTPException(status_code=404, detail=f"Transação {transaction_id} não encontrada")

    db.delete(transacao)
    db.commit()
    return {"mensagem": f"Transação {transaction_id} removida com sucesso"}


def db_media_valor_conta(db: Session, conta: str) -> Optional[float]:
    """Calcula a média histórica de valor para uma conta."""
    return db.query(func.avg(Transacao.valor)).filter(Transacao.conta == conta).scalar()


# ---------------------------------------------------------------------------
# Anomalias
# ---------------------------------------------------------------------------

def db_criar_anomalia(
    db: Session, id_transacao: int, risco_score: int, classificacao: str, motivo: str
) -> Anomalia:
    """Persiste um registro de anomalia."""
    anomalia = Anomalia(
        id_transacao=id_transacao,
        risco_score=risco_score,
        classificacao=classificacao,
        motivo=motivo
    )
    db.add(anomalia)
    db.commit()
    db.refresh(anomalia)
    return anomalia


def db_listar_anomalias(
    db: Session, skip: int = 0, limit: int = 100, id_transacao: Optional[int] = None
) -> list[Anomalia]:
    """Lista anomalias registradas."""
    query = db.query(Anomalia)
    if id_transacao is not None:
        query = query.filter(Anomalia.id_transacao == id_transacao)
    return query.offset(skip).limit(limit).all()


def db_buscar_anomalia_por_id(db: Session, anomalia_id: int) -> Anomalia:
    """Busca anomalia pelo ID ou lança HTTP 404."""
    anomalia = db.query(Anomalia).filter(Anomalia.id_analise == anomalia_id).first()

    if not anomalia:
        raise HTTPException(status_code=404, detail=f"Anomalia {anomalia_id} não encontrada")
    return anomalia


# ---------------------------------------------------------------------------
# Regras de Fraude
# ---------------------------------------------------------------------------

def db_listar_regras_ativas(db: Session) -> list[RegraFraude]:
    """Retorna apenas as regras com ativa=True."""
    return db.query(RegraFraude).filter(RegraFraude.ativa == True).all()


def db_listar_regras(db: Session) -> list[RegraFraude]:
    """Retorna todas as regras cadastradas."""
    return db.query(RegraFraude).all()


# ---------------------------------------------------------------------------
# Transacao_Regra
# ---------------------------------------------------------------------------

def db_criar_transacao_regra(
    db: Session, id_transacao: int, id_regra: int, acionada: bool
) -> TransacaoRegra:
    """Persiste o resultado de uma regra aplicada a uma transação."""
    registro = TransacaoRegra(
        id_transacao=id_transacao,
        id_regra=id_regra,
        acionada=acionada
    )
    db.add(registro)
    return registro


# ---------------------------------------------------------------------------
# Seed — população inicial do banco
# ---------------------------------------------------------------------------

def seed_regras(db: Session) -> None:
    """Insere as regras padrão se a tabela estiver vazia."""
    if db.query(RegraFraude).count() > 0:
        return
    for r in REGRAS_PADRAO:
        db.add(RegraFraude(**r))
    db.commit()
    print(f"[seed] {len(REGRAS_PADRAO)} regras inseridas.")


def seed_transacoes(db: Session) -> None:
    """Importa o JSON de treino se a tabela de transações estiver vazia."""
    if db.query(Transacao).count() > 0:
        print(f"[seed] Banco já populado com {db.query(Transacao).count()} transações.")
        return

    if not os.path.exists(JSON_TREINO):
        print(f"[seed] Arquivo não encontrado: {JSON_TREINO}")
        return

    print(f"[seed] Importando: {JSON_TREINO}")
    df = pd.read_json(JSON_TREINO)

    df["data"]        = df["data"].astype(str)
    df["hora"]        = df["hora"].astype(str)
    df["data_hora"]   = pd.to_datetime(df["data"] + " " + df["hora"], errors="coerce")
    df["localizacao"] = df["cidade"] + ", " + df["estado"] + ", " + df["pais"]
    df["canal"]       = df["dispositivo"]
    df["descricao"]   = "Transação importada do dataset"

    colunas_validas = [
        "conta", "valor", "tipo_transacao", "data_hora", "localizacao",
        "dispositivo", "canal", "descricao", "data", "hora", "dia_semana",
        "categoria", "cidade", "estado", "pais", "latitude", "longitude",
        "estabelecimento", "tentativas", "ip_origem", "is_fraude"
    ]
    df = df[[c for c in colunas_validas if c in df.columns]]

    # Importação local para evitar import circular (repository <--> service)
    from services.anomaly_detection import executar_deteccao

    transacoes_adicionadas = 0
    anomalias_detectadas = 0

    # Iterar sobre o dataframe para inserir via SQLAlchemy e acionar regras
    for _, row in df.iterrows():
        dados = row.where(pd.notnull(row), None).to_dict()
        transacao = db_criar_transacao(db, dados)
        
        # Opcional: avaliar anomalias assim como seria no endpoint POST
        is_anomalia = executar_deteccao(db, transacao)
        
        transacoes_adicionadas += 1
        if is_anomalia:
            anomalias_detectadas += 1

    print(f"[seed] {transacoes_adicionadas} transações importadas. {anomalias_detectadas} anomalias detectadas.")
