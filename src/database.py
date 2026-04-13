from datetime import date, time as time_obj
import os
from typing import Optional
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, Date, Time, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends
import sqlite3
import pandas as pd
from pydantic import BaseModel

app = FastAPI()

DATABASE_URL = "sqlite:///./transacoes_db.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Transacoes(Base):
    __tablename__ = "transacoes"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    dia_semana = Column(String, nullable=False)
    categoria = Column(String, nullable=False)
    conta = Column(String, nullable=False)
    cidade = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    pais = Column(String, nullable=False)
    latitude = Column(String, nullable=False)
    longitude = Column(String, nullable=False)
    tipo_transacao = Column(String, nullable=False)
    dispositivo = Column(String, nullable=False)
    estabelecimento = Column(String, nullable=False)
    tentativas = Column(Integer, nullable=False)
    ip_origem = Column(String, nullable=False)
    is_fraude = Column(Boolean, nullable=False)
    verifica_fraude = Column(Boolean)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TransacoesResponse(BaseModel):
    id: int
    valor: float
    data: date
    hora: time_obj
    dia_semana: str
    categoria: str
    conta: str
    cidade: str
    estado: str
    pais: str
    latitude: str
    longitude: str
    tipo_transacao: str
    dispositivo: str
    estabelecimento: str
    tentativas: int
    ip_origem: str
    is_fraude: bool
    verifica_fraude: Optional[bool] = None

class TransacoesCreate(BaseModel):
    valor: float
    data: date
    hora: time_obj
    dia_semana: str
    categoria: str
    conta: str
    cidade: str
    estado: str
    pais: str
    latitude: str
    longitude: str
    tipo_transacao: str
    dispositivo: str
    estabelecimento: str
    tentativas: int
    ip_origem: str
    is_fraude: bool

def popular_banco_se_vazio():
    db = SessionLocal()
    if db.query(Transacoes).count() == 0:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        caminho_json = os.path.join(base_dir, 'data', 'transacoes_treino.json')

        if os.path.exists(caminho_json):
            df = pd.read_json(caminho_json)
            
            # Aplica regras no DataFrame antes de salvar
            df['hora_obj'] = pd.to_datetime(df['hora']).dt.time
            media_por_conta = df.groupby('conta')['valor'].transform('mean')
            
            condicao_hora = ((df['hora_obj'] >= time_obj(22, 0)) | (df['hora_obj'] <= time_obj(5, 0))) & (df['valor'] > 500)
            condicao_tentativas = df['tentativas'] >= 2
            condicao_media = df['valor'] > (media_por_conta * 3)
            
            df['verifica_fraude'] = condicao_hora | condicao_tentativas | condicao_media
            df = df.drop(columns=['hora_obj'])
            
            conn = sqlite3.connect('transacoes_db.db')
            df.to_sql('transacoes', conn, if_exists='append', index=False)
            conn.close()

    db.close()

def verificar_fraude_regras(db: Session, conta: str, valor: float, hora: time_obj, tentativas: int) -> bool:
    fraude_detectada = False

    # Remove o fuso horário (tzinfo) se existir, para permitir a comparação com time_obj naive
    hora_naive = hora.replace(tzinfo=None)

    # Regra 1: Horário (22h - 05h)
    if hora_naive >= time_obj(22, 0) or hora_naive <= time_obj(5, 0):
        if valor > 500:
            fraude_detectada = True

    # Regra 2: Tentativas
    if tentativas >= 2:
        fraude_detectada = True

    # Regra 3: Valor acima da média da conta
    media_valores = db.query(func.avg(Transacoes.valor))\
        .filter(Transacoes.conta == conta)\
        .scalar()

    if media_valores and valor > media_valores * 3:
        fraude_detectada = True

    return fraude_detectada

popular_banco_se_vazio()

@app.get("/transactions/{transaction_id}", response_model=TransacoesResponse)
def ler_transaction_id(transaction_id: int, db: Session = Depends(get_db)):
    transacao = db.query(Transacoes).filter(Transacoes.id == transaction_id).first()
    if not transacao:
        return {"error": "Transação não encontrada"}
    return transacao

@app.post("/transactions/", response_model=TransacoesResponse)
def criar_transacao(transacao: TransacoesCreate, db: Session = Depends(get_db)):

    fraude_detectada = verificar_fraude_regras(
        db=db,
        conta=transacao.conta,
        valor=transacao.valor,
        hora=transacao.hora,
        tentativas=transacao.tentativas
    )

    db_transacao = Transacoes(
        **transacao.model_dump(),
        verifica_fraude=fraude_detectada
    )

    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)

    return db_transacao

@app.get("/transactions", response_model=list[TransacoesResponse])
def ler_transacoes(
    skip: int = 0,
    limit: int = 100,
    categoria: Optional[str] = None,
    conta: Optional[str] = None,
    cidade: Optional[str] = None,
    tipo_transacao: Optional[str] = None,
    valor_minimo: Optional[float] = None,
    valor_maximo: Optional[float] = None,
    is_fraude: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Transacoes)

    if categoria:
        query = query.filter(Transacoes.categoria == categoria)
    if conta:
        query = query.filter(Transacoes.conta == conta)
    if cidade:
        query = query.filter(Transacoes.cidade == cidade)
    if tipo_transacao:
        query = query.filter(Transacoes.tipo_transacao == tipo_transacao)
    if valor_minimo is not None:
        query = query.filter(Transacoes.valor >= valor_minimo)
    if valor_maximo is not None:
        query = query.filter(Transacoes.valor <= valor_maximo)
    if is_fraude is not None:
        query = query.filter(Transacoes.is_fraude == is_fraude)

    return query.offset(skip).limit(limit).all()

@app.get("/anomalies", response_model=list[TransacoesResponse])
def ler_anomalias(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Transacoes).filter(Transacoes.verifica_fraude == True)
    return query.offset(skip).limit(limit).all()