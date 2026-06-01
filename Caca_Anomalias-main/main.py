"""
Módulo: main.py
Descrição: Ponto de entrada da aplicação Caça Anomalias.
           Inicializa o FastAPI, cria as tabelas e popula o banco.

           Para rodar: uvicorn main:app --reload
           Documentação: http://localhost:8000/docs
Autor: Squad 4
Data: 2026
"""

from fastapi import FastAPI

from core.database import engine, Base, SessionLocal
from models.models import Transacao, Anomalia, RegraFraude, TransacaoRegra  # noqa: F401
from controllers.transaction_controller import router as transaction_router
from controllers.anomaly_controller import router as anomaly_router
from controllers.llm_controller import router as llm_router

from repositories.data_repository import seed_regras, seed_transacoes

# Cria as 4 tabelas no banco se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Caça Anomalias API",
    description=(
        "Sistema de detecção de anomalias em transações financeiras bancárias.\n\n"
        "**Tabelas:** Transacao · Anomalia · Regra_Fraude · Transacao_Regra\n\n"
        "Squad 4 — Residência em Software — 2026."
    ),
    version="5.0.0"
)

app.include_router(transaction_router)
app.include_router(anomaly_router)
app.include_router(llm_router)


@app.on_event("startup")
def startup_event():
    """Popula banco com regras e transações de treino na primeira execução."""
    db = SessionLocal()
    try:
        seed_regras(db)
        seed_transacoes(db)
    finally:
        db.close()


@app.get("/", tags=["Health"])
def root():
    return {"sistema": "Caça Anomalias", "versao": "5.0.0", "status": "online", "documentacao": "/docs"}


@app.get("/ping", tags=["Health"])
def ping():
    return {"status": "pong"}
