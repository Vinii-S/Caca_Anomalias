from datetime import date, time
import os
from typing import Optional
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
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
    id = Column(Integer, primary_key=True, index=True, nullable=False, autoincrement=True)
    valor = Column(Float, index=True, nullable=False)
    data = Column(Date, index=True, nullable=False)
    hora = Column(Time, index=True, nullable=False)
    dia_semana = Column(String, index=True, nullable=False)
    categoria = Column(String, index=True, nullable=False)
    conta = Column(String, index=True, nullable=False)
    cidade = Column(String, index=True, nullable=False)
    estado = Column(String, index=True, nullable=False)
    pais = Column(String, index=True, nullable=False)
    latitude = Column(String, index=True, nullable=False)
    longitude = Column(String, index=True, nullable=False)
    tipo_transacao = Column(String, index=True, nullable=False)
    dispositivo = Column(String, index=True, nullable=False)
    estabelecimento = Column(String, index=True, nullable=False)
    tentativas = Column(Integer, index=True, nullable=False)
    ip_origem = Column(String, index=True, nullable=False)
    is_fraude = Column(Boolean, index=True, nullable=False)
    verifica_fraude = Column(Boolean, index=True)
	
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
    hora: time
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
    hora: time
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
    
def popular_banco_se_vazio():
    db = SessionLocal()
    quantidade = db.query(Transacoes).count()
    if quantidade == 0:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        caminho_json = os.path.join(base_dir, 'data', 'transacoes_treino.json')
        df = pd.read_json(caminho_json)
        conn = sqlite3.connect('transacoes_db.db')
        df.to_sql('transacoes', conn, if_exists='append', index=False, chunksize=1000)
        conn.close()
    db.close()

popular_banco_se_vazio()

@app.get("/transactions/{transaction_id}", response_model=TransacoesResponse)
def ler_transaction_id(transaction_id: int, db: Session = Depends(get_db)):
    transacao = db.query(Transacoes).filter(Transacoes.id == transaction_id).first()
    if transacao is None:
        return {"error": "Transação não encontrada"}
    return transacao

@app.post("/transactions/", response_model=TransacoesResponse)
def criar_transacao(transacao: TransacoesCreate, db: Session = Depends(get_db)):
    db_transacao = Transacoes(**transacao.model_dump())
    db.add(db_transacao)
    db.commit()
    db.refresh(db_transacao)
    return db_transacao

@app.get("/transactions", response_model=list[TransacoesResponse])
def ler_transacoes(skip: int = 0, limit: int = 10, categoria: Optional [str] = None, conta: Optional[str] = None, cidade: Optional[str] = None, tipo_transacao: Optional[str] = None, valor_minimo: Optional[float] = None, valor_maximo: Optional[float] = None, db: Session = Depends(get_db)):
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

    transacoes = query.offset(skip).limit(limit).all()
    return transacoes