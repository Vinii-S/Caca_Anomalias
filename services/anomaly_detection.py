"""
Módulo: services/anomaly_detection.py
Descrição: Serviço de detecção de anomalias. Contém EXCLUSIVAMENTE a
           lógica de negócio — decide se uma transação é suspeita,
           calcula o risco_score e orquestra as chamadas ao repository.
           Não acessa o banco diretamente nem conhece HTTP.
           (Regra 1 do documento: lógica de negócio centralizada no Service)
Autor: Squad 4
Data: 2026
"""
import json
import pandas as pd
from sklearn.ensemble import IsolationForest

# =========================================================
# TREINAMENTO DO ISOLATION FOREST
# =========================================================

with open("data/transacoes_treino.json", "r", encoding="utf-8") as arquivo:
    dados_treino = json.load(arquivo)

dados_processados = []

for item in dados_treino:

    try:
        hora = int(item["hora"].split(":")[0])
    except:
        hora = 0

    dados_processados.append({
        "valor": item["valor"],
        "tentativas": item["tentativas"],
        "latitude": float(item["latitude"]),
        "longitude": float(item["longitude"]),
        "hora": hora
    })

df_treino = pd.DataFrame(dados_processados)

modelo_iforest = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42
)

modelo_iforest.fit(df_treino)


from datetime import time as time_obj
from sqlalchemy.orm import Session

from core.config import (
    LIMIAR_HORA_FIM, LIMIAR_HORA_INICIO,
    LIMIAR_MEDIA, LIMIAR_TENTATIVAS,
    LIMIAR_VALOR_NOTURNO, PESOS_REGRA,
)
from models.models import Transacao
from repositories.data_repository import (
    db_criar_anomalia,
    db_criar_transacao_regra,
    db_listar_anomalias,
    db_listar_regras_ativas,
    db_media_valor_conta,
)


def _classificar_risco(score: int) -> str:
    """Converte risco_score numérico em classificação textual (RN19)."""
    if score >= 70:
        return "Alto"
    elif score >= 40:
        return "Médio"
    return "Baixo"


def _parse_hora(hora_str: str) -> time_obj:
    """Converte string de hora para objeto time com segurança."""
    try:
        partes = hora_str.split(":")
        return time_obj(int(partes[0]), int(partes[1]))
    except Exception:
        return time_obj(0, 0)


def executar_deteccao(db: Session, transacao: Transacao) -> bool:
    """
    Executa todas as regras ativas sobre a transação (RF04).

    Responsabilidades deste método (Service):
        - Buscar regras ativas (via repository)
        - Avaliar cada regra com base nos dados da transação
        - Calcular risco_score e classificacao
        - Orquestrar o registro dos resultados (via repository)

    Parâmetros:
        db        -- Sessão ativa do banco
        transacao -- Objeto Transacao já persistido

    Retorna:
        True se anomalia detectada, False caso contrário
    """

    regras_ativas = db_listar_regras_ativas(db)
    hora_obj      = _parse_hora(str(transacao.hora or "00:00"))
    tentativas    = transacao.tentativas or 0
    media_conta   = db_media_valor_conta(db, transacao.conta)

    score_total = 0
    motivos     = []

    for regra in regras_ativas:
        acionada = False

        # Regra 1 — Horário noturno de alto valor
        if regra.tipo_regra == "horario":
            if hora_obj >= time_obj(LIMIAR_HORA_INICIO, 0) or hora_obj <= time_obj(LIMIAR_HORA_FIM, 0):
                if transacao.valor > LIMIAR_VALOR_NOTURNO:
                    acionada = True
                    motivos.append(
                        f"{regra.nome}: R$ {transacao.valor:.2f} às {hora_obj.strftime('%H:%M')}h"
                    )
                    score_total += PESOS_REGRA.get("horario", 0)

        # Regra 2 — Múltiplas tentativas
        elif regra.tipo_regra == "tentativas":
            if tentativas >= LIMIAR_TENTATIVAS:
                acionada = True
                motivos.append(f"{regra.nome}: {tentativas} tentativas")
                score_total += PESOS_REGRA.get("tentativas", 0)

        # Regra 3 — Valor acima de N vezes a média histórica da conta
        elif regra.tipo_regra == "valor_medio":
            if media_conta and transacao.valor > media_conta * LIMIAR_MEDIA:
                acionada = True
                motivos.append(
                    f"{regra.nome}: R$ {transacao.valor:.2f} excede "
                    f"{LIMIAR_MEDIA:.0f}x a média (R$ {media_conta:.2f})"
                )
                score_total += PESOS_REGRA.get("valor_medio", 0)

        # Persiste o resultado desta regra via repository
        db_criar_transacao_regra(
            db=db,
            id_transacao=transacao.id_transacao,
            id_regra=regra.id_regra,
            acionada=acionada
        )

    db.commit()
    
    # =====================================================
    # DETECÇÃO COM ISOLATION FOREST
    # =====================================================

    try:

        hora_nova = int(str(transacao.hora).split(":")[0])

        dados_novos = pd.DataFrame([{
            "valor": transacao.valor,
            "tentativas": transacao.tentativas,
            "latitude": float(transacao.latitude),
            "longitude": float(transacao.longitude),
            "hora": hora_nova
        }])

        predicao = modelo_iforest.predict(dados_novos)

        score_iforest = modelo_iforest.decision_function(dados_novos)

        # -1 = anomalia
        if predicao[0] == -1:

            motivos.append(
                f"O Sistema detectou comportamento anômalo "
                f"(score={score_iforest[0]:.4f})"
            )

            score_total += 40

    except Exception as exc:
        print("Erro no Sistema (Isolation Forest):", exc)
        
    print("ANOMALIA DETECTADA")
    print(score_total)
    print(motivos)

    # Se alguma regra foi acionada, registra a anomalia via repository
    if score_total > 0:
        score_final = min(score_total, 100)
        print("SALVANDO ANOMALIA NO BANCO")
        db_criar_anomalia(
            db=db,
            id_transacao=transacao.id_transacao,
            risco_score=score_final,
            classificacao=_classificar_risco(score_final),
            motivo=" | ".join(motivos)
        )
        return True

    return False


def listar_anomalias(db: Session, skip: int = 0, limit: int = 100):
    """Delega listagem de anomalias ao repository."""
    return db_listar_anomalias(db=db, skip=skip, limit=limit)
