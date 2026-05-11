"""
Módulo: main.py
Descrição: Ponto de entrada da aplicação Caça Anomalias.
           Inicializa o FastAPI, registra os routers e popula
           o banco na primeira execução.

           Para rodar: uvicorn main:app --reload
           Documentação: http://localhost:8000/docs

Autor: Squad 4
Data: 2026
"""

from fastapi import FastAPI

from models.database import engine
from models.transacao import Base

from routers import route_anomalies, route_transactions
from controllers.popular_banco import popular_banco_se_vazio

# Cria as tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Caça Anomalias API",
    description=(
        "Sistema de detecção de anomalias em transações financeiras bancárias. "
        "Squad 4 — Residência em Software — 2026."
    ),
    version="2.0.0"
)

# Routers
app.include_router(route_transactions.router)
app.include_router(route_anomalies.router)


@app.on_event("startup")
def startup_event():
    popular_banco_se_vazio()


@app.get("/", tags=["Health"])
def root():
    return {
        "sistema": "Caça Anomalias",
        "versao": "2.0.0",
        "status": "online",
        "documentacao": "/docs"
    }


@app.get("/ping", tags=["Health"])
def ping():
    return {"status": "pong"}
