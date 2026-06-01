"""
Módulo: services/transaction_service.py
Descrição: Serviço de transações. Orquestra a criação de uma transação:
           transforma os dados de entrada (schema) no formato do banco,
           delega a persistência ao repository e aciona o serviço de detecção.
           (Regra 1: lógica de negócio centralizada no Service, não no Controller)
Autor: Squad 4
Data: 2026
"""

from datetime import datetime
from sqlalchemy.orm import Session

from repositories.data_repository import db_criar_transacao
from schemas.schemas import TransacaoCreate
from services.anomaly_detection import executar_deteccao


def processar_criacao_transacao(db: Session, dados: TransacaoCreate):
    """
    Orquestra a criação de uma transação (RF01, RF04).

    Responsabilidades deste método (Service):
        1. Transformar dados do schema em payload para o banco
        2. Construir campos derivados (data_hora, localizacao, canal)
        3. Delegar a persistência ao repository
        4. Acionar a detecção de anomalias

    Parâmetros:
        db    -- Sessão ativa do banco
        dados -- Schema de entrada validado pelo Controller

    Retorna:
        Objeto Transacao persistido
    """

    # Constrói campos derivados do diagrama a partir dos dados de entrada
    try:
        data_hora = datetime.combine(dados.data, dados.hora)
    except Exception:
        data_hora = None

    payload = dict(
        conta           = dados.conta,
        valor           = dados.valor,
        tipo_transacao  = dados.tipo_transacao,
        data_hora       = data_hora,
        localizacao     = f"{dados.cidade}, {dados.estado}, {dados.pais}",
        dispositivo     = dados.dispositivo,
        canal           = dados.canal or dados.dispositivo,
        descricao       = dados.descricao,
        data            = str(dados.data),
        hora            = str(dados.hora),
        dia_semana      = dados.dia_semana,
        categoria       = dados.categoria,
        cidade          = dados.cidade,
        estado          = dados.estado,
        pais            = dados.pais,
        latitude        = dados.latitude,
        longitude       = dados.longitude,
        estabelecimento = dados.estabelecimento,
        tentativas      = dados.tentativas,
        ip_origem       = dados.ip_origem,
        is_fraude       = dados.is_fraude,
    )

    # Delega persistência ao repository
    transacao = db_criar_transacao(db=db, dados=payload)

    # Aciona o serviço de detecção de anomalias
    executar_deteccao(db=db, transacao=transacao)

    return transacao
