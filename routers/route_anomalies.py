"""
Módulo: routers/anomalies.py
Descrição: Define a rota HTTP para consulta de anomalias detectadas.
           Delega toda a lógica ao transaction_ctrl.py.

Rotas:
    GET /anomalies   -- RF03: Consultar Anomalias Detectadas
Autor: Squad 4
Data: 2026
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import TransacaoResponse
from models.transacao import Transacao

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalias"]
)


@router.get(
    "",
    response_model=list[TransacaoResponse],
    summary="RF03 — Consultar Anomalias Detectadas",
    description=(
        "Retorna apenas as transações sinalizadas como suspeitas "
        "pelo motor de detecção (verifica_fraude = True)."
    )
)
def listar_anomalias(
    skip:  int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return (
        db.query(Transacao)
        .filter(Transacao.verifica_fraude == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
