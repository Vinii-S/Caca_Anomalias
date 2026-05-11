"""
Módulo: anomaly_ctrl.py
Descrição: Encapsula a lógica de detecção de anomalias (RF04 — Executar Regras
           de Detecção). As três regras foram extraídas do database.py original
           e organizadas aqui como responsabilidade única.
Autor: Squad 4
Data: 2026
"""

from datetime import time as time_obj
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.transacao import Transacao


def verificar_fraude_regras(
    db: Session,
    conta: str,
    valor: float,
    hora: time_obj,
    tentativas: int
) -> bool:
    """
    Executa as três regras de detecção de anomalia sobre uma transação (RF04).

    Regra 1 — Horário noturno de alto valor:
        Transações acima de R$ 500 entre 22h e 05h são sinalizadas.

    Regra 2 — Múltiplas tentativas:
        Duas ou mais tentativas indicam comportamento suspeito.

    Regra 3 — Valor acima de 3x a média histórica da conta:
        Desvio estatístico em relação ao comportamento habitual do usuário.

    Parâmetros:
        db         -- Sessão ativa do banco de dados
        conta      -- Identificador da conta do cliente
        valor      -- Valor da transação
        hora       -- Horário da transação
        tentativas -- Número de tentativas

    Retorna:
        True se qualquer regra for acionada, False caso contrário
    """

    fraude_detectada = False

    # Remove timezone se presente (compatibilidade com Pydantic v2)
    hora_naive = hora.replace(tzinfo=None) if hasattr(hora, 'tzinfo') else hora

    # Regra 1: Transação noturna de alto valor
    if hora_naive >= time_obj(22, 0) or hora_naive <= time_obj(5, 0):
        if valor > 500:
            fraude_detectada = True

    # Regra 2: Múltiplas tentativas
    if tentativas >= 2:
        fraude_detectada = True

    # Regra 3: Valor acima de 3x a média histórica da conta
    media_conta = (
        db.query(func.avg(Transacao.valor))
        .filter(Transacao.conta == conta)
        .scalar()
    )
    if media_conta and valor > media_conta * 3:
        fraude_detectada = True

    return fraude_detectada
