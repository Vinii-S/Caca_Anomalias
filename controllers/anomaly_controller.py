"""
Módulo: controllers/anomaly_controller.py
Descrição: Controller de anomalias. Responsabilidades únicas:
             1. Receber a requisição HTTP
             2. Chamar o Service / Repository
             3. Retornar a resposta JSON
           SEM lógica de negócio aqui (regra 1 do documento).
Autor: Squad 4
Data: 2026
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.schemas import AnomaliaResponse, RegraFraudeResponse
from services.anomaly_detection import listar_anomalias
from repositories.data_repository import db_buscar_anomalia_por_id, db_listar_regras

router = APIRouter(tags=["Anomalias e Regras"])


@router.get(
    "/anomalies",
    response_model=list[AnomaliaResponse],
    summary="RF03 — Consultar Anomalias Detectadas"
)
def listar(
    skip: int = 0,
    limit: int = 100,
    id_transacao: Optional[int] = None,
    db: Session = Depends(get_db)
):
    return listar_anomalias(db=db, skip=skip, limit=limit, id_transacao=id_transacao)


@router.get(
    "/anomalies/{anomalia_id}",
    response_model=AnomaliaResponse,
    summary="RF03 — Consultar Anomalia por ID"
)
def buscar_anomalia(anomalia_id: int, db: Session = Depends(get_db)):
    return db_buscar_anomalia_por_id(db=db, anomalia_id=anomalia_id)


@router.get(
    "/regras",
    response_model=list[RegraFraudeResponse],
    summary="Listar Regras de Fraude"
)
def listar_regras(db: Session = Depends(get_db)):
    return db_listar_regras(db=db)
