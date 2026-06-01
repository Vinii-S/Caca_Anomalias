"""
Módulo: controllers/llm_controller.py
Descrição: Controller responsável pelos endpoints de explicação por LLM.
Autor: Squad 4
Data: 2026
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.schemas import ExplicacaoLLMResponse
from services.llm_service import gerar_explicacao_anomalia

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.get(
    "/anomalies/{anomalia_id}/explain",
    response_model=ExplicacaoLLMResponse,
    summary="RF07 — Explicar Anomalia com LLM",
    description="Gera uma explicação textual da anomalia usando uma LLM local via Ollama."
)
def explicar_anomalia(anomalia_id: int, db: Session = Depends(get_db)):
    return gerar_explicacao_anomalia(db=db, anomalia_id=anomalia_id)