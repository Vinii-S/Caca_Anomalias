"""
Módulo: controllers/transaction_controller.py
Descrição: Controller de transações. Responsabilidades únicas:
             1. Receber a requisição HTTP
             2. Validar entrada via Schema (automático pelo FastAPI)
             3. Chamar o Service correspondente
             4. Retornar a resposta JSON
           SEM lógica de negócio aqui (regra 1 do documento).
Autor: Squad 4
Data: 2026
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.schemas import TransacaoCreate, TransacaoResponse
from services.transaction_service import processar_criacao_transacao
from repositories.data_repository import (
    db_buscar_transacao_por_id,
    db_excluir_transacao,
    db_listar_transacoes,
)

router = APIRouter(prefix="/transactions", tags=["Transações"])


@router.post(
    "/",
    response_model=TransacaoResponse,
    status_code=201,
    summary="RF01 — Registrar Transação Financeira",
    description="Recebe dados, valida via Schema e delega ao TransactionService."
)
def criar_transacao(dados: TransacaoCreate, db: Session = Depends(get_db)):
    return processar_criacao_transacao(db=db, dados=dados)


@router.get(
    "",
    response_model=list[TransacaoResponse],
    summary="RF05 — Consultar Histórico de Transações"
)
def listar_transacoes(
    skip:           int             = 0,
    limit:          int             = 100,
    categoria:      Optional[str]   = None,
    conta:          Optional[str]   = None,
    cidade:         Optional[str]   = None,
    tipo_transacao: Optional[str]   = None,
    valor_minimo:   Optional[float] = None,
    valor_maximo:   Optional[float] = None,
    is_fraude:      Optional[bool]  = None,
    db: Session = Depends(get_db)
):
    return db_listar_transacoes(
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
    return db_buscar_transacao_por_id(db=db, transaction_id=transaction_id)


@router.delete(
    "/{transaction_id}",
    summary="RF06 — Excluir Registro de Transação"
)
def excluir_transacao(transaction_id: int, db: Session = Depends(get_db)):
    return db_excluir_transacao(db=db, transaction_id=transaction_id)
