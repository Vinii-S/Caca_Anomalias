from datetime import date, time
import os
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import sqlite3
import pandas as pd
from pydantic import BaseModel

app = FastAPI()
DATABASE_URL = "sqlite:///./test.db"
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

def popular_banco_se_vazio():
    db = SessionLocal()
    quantidade = db.query(Transacoes).count()
    if quantidade == 0:
        df = pd.read_json(os.path.join(os.path.dirname(__file__), '../transacoes_treino.json'))
        conn = sqlite3.connect('test.db')
        df.to_sql('transacoes', conn, if_exists='append', index=False, chunksize=1000)
        conn.close()
    db.close()

popular_banco_se_vazio()

@app.get("/transacoes", response_model=list[TransacoesResponse])
def ler_transacoes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transacoes = db.query(Transacoes).offset(skip).limit(limit).all()
    return transacoes