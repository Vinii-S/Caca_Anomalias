"""
Módulo: schemas/schemas.py
Descrição: Define os schemas Pydantic de validação de entrada e saída da API.
           Separado dos modelos ORM (regras 4 e 5 do documento) para:
             - desacoplar a API das entidades do banco
             - evitar expor estruturas internas ao frontend
             - garantir validação rigorosa de tipos (RN01, RN02, RN03)
             - melhorar a documentação automática no Swagger
Autor: Squad 4
Data: 2026
"""

from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas de Transacao
# ---------------------------------------------------------------------------

class TransacaoCreate(BaseModel):
    """
    Schema de entrada para criação de transação (RF01).
    Valida todos os campos antes de chegar ao Service (RN01, RN02, RN03).
    """

    valor:           float         = Field(..., gt=0,   description="Valor > zero (RN03)")
    data:            date          = Field(...,          description="Data (YYYY-MM-DD)")
    hora:            time          = Field(...,          description="Hora (HH:MM:SS)")
    dia_semana:      str           = Field(...,          description="Dia da semana")
    categoria:       str           = Field(...,          description="Categoria da transação")
    conta:           str           = Field(...,          description="Identificador da conta")
    cidade:          str           = Field(...,          description="Cidade de origem")
    estado:          str           = Field(...,          description="Estado (UF)")
    pais:            str           = Field(...,          description="País")
    latitude:        str           = Field(...,          description="Latitude geográfica")
    longitude:       str           = Field(...,          description="Longitude geográfica")
    tipo_transacao:  str           = Field(...,          description="Modalidade (PIX, Débito)")
    dispositivo:     str           = Field(...,          description="Dispositivo utilizado")
    estabelecimento: str           = Field(...,          description="Nome do estabelecimento")
    tentativas:      int           = Field(..., ge=1,   description="Nº de tentativas")
    ip_origem:       str           = Field(...,          description="IP de origem")
    is_fraude:       bool          = Field(False,        description="Rótulo do dataset")
    canal:           Optional[str] = Field(None,         description="Canal (Mobile, Web, ATM)")
    descricao:       Optional[str] = Field(None,         description="Descrição da operação")

    class Config:
        json_schema_extra = {
            "example": {
                "valor": 1500.00, "data": "2026-05-11", "hora": "23:30:00",
                "dia_semana": "Segunda", "categoria": "Transferência",
                "conta": "CC-001", "cidade": "São Paulo", "estado": "SP",
                "pais": "Brasil", "latitude": "-23.5505", "longitude": "-46.6333",
                "tipo_transacao": "PIX", "dispositivo": "Mobile",
                "estabelecimento": "Banco XYZ", "tentativas": 3,
                "ip_origem": "192.168.1.100", "is_fraude": False,
                "canal": "Mobile", "descricao": "Transferência para fornecedor"
            }
        }


class TransacaoResponse(BaseModel):
    """Schema de saída para uma transação — expõe apenas o necessário ao frontend."""

    id_transacao:    int
    conta:           Optional[str]      = None
    valor:           float
    tipo_transacao:  Optional[str]      = None
    data_hora:       Optional[datetime] = None
    localizacao:     Optional[str]      = None
    dispositivo:     Optional[str]      = None
    canal:           Optional[str]      = None
    descricao:       Optional[str]      = None
    data:            Optional[str]      = None
    hora:            Optional[str]      = None
    dia_semana:      Optional[str]      = None
    categoria:       Optional[str]      = None
    cidade:          Optional[str]      = None
    estado:          Optional[str]      = None
    pais:            Optional[str]      = None
    estabelecimento: Optional[str]      = None
    tentativas:      Optional[int]      = None
    ip_origem:       Optional[str]      = None
    is_fraude:       bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Schemas de Anomalia
# ---------------------------------------------------------------------------

class AnomaliaResponse(BaseModel):
    """Schema de saída para uma anomalia detectada (RF03)."""

    id_analise:    int
    id_transacao:  int
    risco_score:   int
    classificacao: str
    motivo:        str
    data_analise:  Optional[datetime] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Schemas de RegraFraude
# ---------------------------------------------------------------------------

class RegraFraudeResponse(BaseModel):
    """Schema de saída para uma regra de fraude cadastrada."""

    id_regra:   int
    nome:       str
    descricao:  str
    tipo_regra: str
    ativa:      bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Schemas de TransacaoRegra
# ---------------------------------------------------------------------------

class TransacaoRegraResponse(BaseModel):
    """Schema de saída para o registro de acionamento de regra por transação."""

    id_transacao_regra: int
    id_transacao:       int
    id_regra:           int
    acionada:           bool
    data_acionamento:   Optional[datetime] = None

    class Config:
        from_attributes = True
