"""
Módulo: core/risk_rules.py
Descrição: Funções puras para explicar riscos usando as regras do projeto.
           O objetivo é compartilhar a mesma leitura de negócio entre
           backend e frontend, sem duplicar condições na interface.
Autor: Squad 4
Data: 2026
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import (
    LIMIAR_HORA_FIM,
    LIMIAR_HORA_INICIO,
    LIMIAR_TENTATIVAS,
    LIMIAR_VALOR_NOTURNO,
)


def _hora_suspeita(hora: Any) -> bool:
    """Retorna True quando a operação cai na janela noturna suspeita."""

    if pd.isna(hora):
        return False

    hora_texto = str(hora)

    try:
        hora_inteira = int(hora_texto.split(":")[0])
    except Exception:
        return False

    return hora_inteira >= LIMIAR_HORA_INICIO or hora_inteira <= LIMIAR_HORA_FIM


def explicar_motivo_alerta(registro: Any) -> str:
    """
    Gera a justificativa visual de risco para um registro de transação.

    Aceita dict, Series ou qualquer objeto com acesso por chave.
    """

    def obter(campo: str, padrao: Any = None) -> Any:
        if isinstance(registro, pd.Series):
            return registro.get(campo, padrao)
        if isinstance(registro, dict):
            return registro.get(campo, padrao)
        return getattr(registro, campo, padrao)

    if int(obter("is_fraude", 0) or 0) == 0:
        return "Transação Segura"

    motivos = []

    if _hora_suspeita(obter("hora")):
        motivos.append("Horário Suspeito")

    try:
        valor = float(obter("valor", 0) or 0)
    except Exception:
        valor = 0.0

    if valor > LIMIAR_VALOR_NOTURNO:
        motivos.append("Valor Atípico")

    try:
        tentativas = int(obter("tentativas", 0) or 0)
    except Exception:
        tentativas = 0

    if tentativas > LIMIAR_TENTATIVAS:
        motivos.append("Múltiplas Tentativas")

    if not motivos:
        motivos.append("Falso negativo")

    return " + ".join(motivos)