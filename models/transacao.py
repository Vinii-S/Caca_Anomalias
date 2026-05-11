"""
Módulo: transacao.py
Descrição: Define o modelo ORM da entidade Transacao, mapeando a tabela
           'transacoes' do banco SQLite. Mantém exatamente os mesmos campos
           do projeto original.
Autor: Squad 4
Data: 2026
"""

from sqlalchemy import Boolean, Column, Integer, String, Float, Date, Time
from models.database import Base


class Transacao(Base):
    """
    Entidade principal do sistema.
    Registra todos os detalhes de uma operação financeira.
    """

    __tablename__ = "transacoes"

    id              = Column(Integer, primary_key=True, index=True, autoincrement=True)
    valor           = Column(Float, nullable=False)
    data            = Column(Date, nullable=False)
    hora            = Column(Time, nullable=False)
    dia_semana      = Column(String, nullable=False)
    categoria       = Column(String, nullable=False)
    conta           = Column(String, nullable=False)
    cidade          = Column(String, nullable=False)
    estado          = Column(String, nullable=False)
    pais            = Column(String, nullable=False)
    latitude        = Column(String, nullable=False)
    longitude       = Column(String, nullable=False)
    tipo_transacao  = Column(String, nullable=False)
    dispositivo     = Column(String, nullable=False)
    estabelecimento = Column(String, nullable=False)
    tentativas      = Column(Integer, nullable=False)
    ip_origem       = Column(String, nullable=False)
    is_fraude       = Column(Boolean, nullable=False, default=False)
    verifica_fraude = Column(Boolean, nullable=True)
