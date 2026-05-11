"""
Módulo: routers/transactions.py
Descrição: Define as rotas HTTP de transações financeiras.
           Delega toda a lógica ao transaction_ctrl.py.

Rotas:
    POST   /transactions/       -- RF01: Registrar Transação
    GET    /transactions        -- RF05: Consultar Histórico
    GET    /transactions/{id}   -- RF05: Consultar por ID
    DELETE /transactions/{id}   -- RF06: Excluir Transação
Autor: Squad 4
Data: 2026
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import TransacaoCreate, TransacaoResponse
from controllers import transactions

router = APIRouter(
    prefix="/transactions",
    tags=["Transações"]
)


@router.post(
    "/",
    response_model=TransacaoResponse,
    status_code=201,
    summary="RF01 — Registrar Transação Financeira"
)
def criar_transacao(dados: TransacaoCreate, db: Session = Depends(get_db)):
    return transactions.criar_transacao(db=db, dados=dados)


@router.get(
    "",
    response_model=list[TransacaoResponse],
    summary="RF05 — Consultar Histórico de Transações"
)
def listar_transacoes(
    skip:           int            = 0,
    limit:          int            = 100,
    categoria:      Optional[str]  = None,
    conta:          Optional[str]  = None,
    cidade:         Optional[str]  = None,
    tipo_transacao: Optional[str]  = None,
    valor_minimo:   Optional[float] = None,
    valor_maximo:   Optional[float] = None,
    is_fraude:      Optional[bool] = None,
    db: Session = Depends(get_db)
):
    return transactions.listar_transacoes(
        db=db, skip=skip, limit=limit,
        categoria=categoria, conta=conta, cidade=cidade,
        tipo_transacao=tipo_transacao,
        valor_minimo=valor_minimo, valor_maximo=valor_maximo,
        is_fraude=is_fraude
    )


@router.get(
    "/{transaction_id}",
    response_model=TransacaoResponse,
    summary="RF05 — Consultar Transação por ID"
)
def buscar_transacao(transaction_id: int, db: Session = Depends(get_db)):
    return transactions.buscar_por_id(db=db, transaction_id=transaction_id)


@router.delete(
    "/{transaction_id}",
    summary="RF06 — Excluir Registro de Transação"
)
def excluir_transacao(transaction_id: int, db: Session = Depends(get_db)):
    return transactions.excluir_transacao(db=db, transaction_id=transaction_id)
