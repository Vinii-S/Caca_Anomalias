"""
Módulo: transaction_ctrl.py
Descrição: Implementa as operações CRUD sobre a entidade Transacao.
           Coordena a criação de transações com a execução automática
           das regras de detecção (RF01, RF05, RF06).
Autor: Squad 4
Data: 2026
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.transacao import Transacao
from models.schemas import TransacaoCreate
from controllers.anomalies import verificar_fraude_regras


def criar_transacao(db: Session, dados: TransacaoCreate) -> Transacao:
    """
    Registra uma nova transação e aplica as regras de detecção (RF01, RF04).

    Parâmetros:
        db    -- Sessão ativa do banco de dados
        dados -- Dados validados da nova transação

    Retorna:
        Objeto Transacao persistido com verifica_fraude preenchido
    """

    fraude_detectada = verificar_fraude_regras(
        db=db,
        conta=dados.conta,
        valor=dados.valor,
        hora=dados.hora,
        tentativas=dados.tentativas
    )

    nova_transacao = Transacao(
        **dados.model_dump(),
        verifica_fraude=fraude_detectada
    )

    db.add(nova_transacao)
    db.commit()
    db.refresh(nova_transacao)

    return nova_transacao


def buscar_por_id(db: Session, transaction_id: int) -> Transacao:
    """
    Busca uma transação pelo ID (RF05).

    Parâmetros:
        db             -- Sessão ativa do banco de dados
        transaction_id -- ID da transação

    Retorna:
        Objeto Transacao ou lança HTTPException 404
    """

    transacao = db.query(Transacao).filter(Transacao.id == transaction_id).first()

    if not transacao:
        raise HTTPException(
            status_code=404,
            detail=f"Transação {transaction_id} não encontrada"
        )

    return transacao


def listar_transacoes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    conta: Optional[str] = None,
    cidade: Optional[str] = None,
    tipo_transacao: Optional[str] = None,
    valor_minimo: Optional[float] = None,
    valor_maximo: Optional[float] = None,
    is_fraude: Optional[bool] = None
) -> list[Transacao]:
    """
    Lista transações com filtros opcionais (RF05, RN09, RN10, RN11).

    Parâmetros:
        db             -- Sessão ativa do banco de dados
        skip           -- Offset de paginação
        limit          -- Máximo de registros retornados
        categoria      -- Filtro por categoria (RN09)
        conta          -- Filtro por conta
        cidade         -- Filtro por cidade (RN10)
        tipo_transacao -- Filtro por modalidade
        valor_minimo   -- Valor mínimo (RN11)
        valor_maximo   -- Valor máximo (RN11)
        is_fraude      -- Filtro por rótulo original

    Retorna:
        Lista de objetos Transacao
    """

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


def excluir_transacao(db: Session, transaction_id: int) -> dict:
    """
    Remove uma transação pelo ID (RF06).
    Operação restrita ao perfil Analista de Dados (admin).

    Parâmetros:
        db             -- Sessão ativa do banco de dados
        transaction_id -- ID da transação a remover

    Retorna:
        Dicionário de confirmação ou lança HTTPException 404
    """

    transacao = db.query(Transacao).filter(Transacao.id == transaction_id).first()

    if not transacao:
        raise HTTPException(
            status_code=404,
            detail=f"Transação {transaction_id} não encontrada para exclusão"
        )

    db.delete(transacao)
    db.commit()

    return {"mensagem": f"Transação {transaction_id} removida com sucesso"}
