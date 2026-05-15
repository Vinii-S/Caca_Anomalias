"""
Módulo: models/models.py
Descrição: Define apenas os modelos ORM (SQLAlchemy) — mapeamento
           das 4 tabelas do banco de dados. Sem schemas Pydantic aqui:
           esses ficam em schemas/schemas.py (regra 4 e 5 do documento).
Autor: Squad 4
Data: 2026
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base


class Transacao(Base):
    """
    Tabela principal: registra cada operação financeira.
    Campos do diagrama: id_transacao, conta, valor, tipo_transacao,
    data_hora, localizacao, dispositivo, canal, descricao.
    Campos complementares do dataset: data, hora, dia_semana, categoria,
    cidade, estado, pais, latitude, longitude, estabelecimento,
    tentativas, ip_origem, is_fraude.
    """

    __tablename__ = "transacoes"

    id_transacao    = Column(Integer,  primary_key=True, index=True, autoincrement=True)
    conta           = Column(String,   nullable=True)
    valor           = Column(Float,    nullable=False)
    tipo_transacao  = Column(String,   nullable=True)
    data_hora       = Column(DateTime, nullable=True)
    localizacao     = Column(String,   nullable=True)
    dispositivo     = Column(String,   nullable=True)
    canal           = Column(String,   nullable=True)
    descricao       = Column(String,   nullable=True)
    data            = Column(String,   nullable=True)
    hora            = Column(String,   nullable=True)
    dia_semana      = Column(String,   nullable=True)
    categoria       = Column(String,   nullable=True)
    cidade          = Column(String,   nullable=True)
    estado          = Column(String,   nullable=True)
    pais            = Column(String,   nullable=True)
    latitude        = Column(String,   nullable=True)
    longitude       = Column(String,   nullable=True)
    estabelecimento = Column(String,   nullable=True)
    tentativas      = Column(Integer,  nullable=True)
    ip_origem       = Column(String,   nullable=True)
    is_fraude       = Column(Boolean,  nullable=False, default=False)

    anomalias         = relationship("Anomalia",       back_populates="transacao")
    transacoes_regras = relationship("TransacaoRegra", back_populates="transacao")


class Anomalia(Base):
    """
    Tabela de anomalias detectadas.
    Campos do diagrama: id_analise, id_transacao (FK), risco_score,
    classificacao, motivo, data_analise.
    """

    __tablename__ = "anomalias"

    id_analise    = Column(Integer,  primary_key=True, index=True, autoincrement=True)
    id_transacao  = Column(Integer,  ForeignKey("transacoes.id_transacao"), nullable=False)
    risco_score   = Column(Integer,  nullable=False)
    classificacao = Column(String,   nullable=False)
    motivo        = Column(String,   nullable=False)
    data_analise  = Column(DateTime, server_default=func.now())

    transacao = relationship("Transacao", back_populates="anomalias")


class RegraFraude(Base):
    """
    Tabela de regras de detecção de fraude.
    Permite ativar/desativar regras sem alterar código.
    Campos do diagrama: id_regra, nome, descricao, tipo_regra, ativa.
    """

    __tablename__ = "regras_fraude"

    id_regra    = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome        = Column(String,  nullable=False, unique=True)
    descricao   = Column(String,  nullable=False)
    tipo_regra  = Column(String,  nullable=False)
    ativa       = Column(Boolean, nullable=False, default=True)

    transacoes_regras = relationship("TransacaoRegra", back_populates="regra")


class TransacaoRegra(Base):
    """
    Tabela de relacionamento N:N entre Transacao e RegraFraude.
    Registra qual regra foi acionada em cada transação.
    Campos do diagrama: id_transacao_regra, id_transacao (FK),
    id_regra (FK), acionada, data_acionamento.
    """

    __tablename__ = "transacoes_regras"

    id_transacao_regra = Column(Integer,  primary_key=True, index=True, autoincrement=True)
    id_transacao       = Column(Integer,  ForeignKey("transacoes.id_transacao"), nullable=False)
    id_regra           = Column(Integer,  ForeignKey("regras_fraude.id_regra"), nullable=False)
    acionada           = Column(Boolean,  nullable=False, default=False)
    data_acionamento   = Column(DateTime, server_default=func.now())

    transacao = relationship("Transacao",   back_populates="transacoes_regras")
    regra     = relationship("RegraFraude", back_populates="transacoes_regras")
