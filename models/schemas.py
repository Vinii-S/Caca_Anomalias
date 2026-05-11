"""
Módulo: schemas.py
Descrição: Define os modelos Pydantic para validação de entrada (RN01, RN02, RN03)
           e serialização de saída da API.
Autor: Squad 4
Data: 2026
"""

from datetime import date, time
from typing import Optional
from pydantic import BaseModel, Field


class TransacaoCreate(BaseModel):
    """
    Schema de entrada para criação de uma nova transação (RF01).
    Todos os campos são obrigatórios conforme RN01 e RN02.
    O valor deve ser maior que zero conforme RN03.
    """

    valor:           float = Field(..., gt=0, description="Valor da transação — deve ser maior que zero (RN03)")
    data:            date  = Field(..., description="Data da transação (YYYY-MM-DD)")
    hora:            time  = Field(..., description="Hora da transação (HH:MM:SS)")
    dia_semana:      str   = Field(..., description="Dia da semana por extenso")
    categoria:       str   = Field(..., description="Categoria da transação")
    conta:           str   = Field(..., description="Identificador da conta")
    cidade:          str   = Field(..., description="Cidade de origem")
    estado:          str   = Field(..., description="Estado (UF)")
    pais:            str   = Field(..., description="País")
    latitude:        str   = Field(..., description="Latitude geográfica")
    longitude:       str   = Field(..., description="Longitude geográfica")
    tipo_transacao:  str   = Field(..., description="Modalidade (PIX, Débito, Crédito)")
    dispositivo:     str   = Field(..., description="Dispositivo utilizado")
    estabelecimento: str   = Field(..., description="Nome do estabelecimento")
    tentativas:      int   = Field(..., ge=1, description="Número de tentativas")
    ip_origem:       str   = Field(..., description="IP de origem da requisição")
    is_fraude:       bool  = Field(default=False, description="Rótulo original do dataset")

    class Config:
        json_schema_extra = {
            "example": {
                "valor": 1500.00,
                "data": "2026-05-11",
                "hora": "23:30:00",
                "dia_semana": "Segunda",
                "categoria": "Transferência",
                "conta": "CC-001",
                "cidade": "São Paulo",
                "estado": "SP",
                "pais": "Brasil",
                "latitude": "-23.5505",
                "longitude": "-46.6333",
                "tipo_transacao": "PIX",
                "dispositivo": "Mobile",
                "estabelecimento": "Banco XYZ",
                "tentativas": 3,
                "ip_origem": "192.168.1.100",
                "is_fraude": False
            }
        }


class TransacaoResponse(BaseModel):
    """
    Schema de saída para uma transação (RF05, RF01).
    Inclui o resultado da detecção de anomalia (verifica_fraude).
    """

    id:              int
    valor:           float
    data:            date
    hora:            time
    dia_semana:      str
    categoria:       str
    conta:           str
    cidade:          str
    estado:          str
    pais:            str
    latitude:        str
    longitude:       str
    tipo_transacao:  str
    dispositivo:     str
    estabelecimento: str
    tentativas:      int
    ip_origem:       str
    is_fraude:       bool
    verifica_fraude: Optional[bool] = None

    class Config:
        from_attributes = True
