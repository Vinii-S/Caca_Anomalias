"""
Módulo: services/llm_service.py
Descrição: Serviço responsável por gerar explicações textuais usando LLM local via Ollama.
"""

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from repositories.data_repository import db_buscar_anomalia_por_id


def montar_prompt_anomalia(anomalia) -> str:
    transacao = anomalia.transacao

    return f"""
Você é um assistente antifraude especializado em transações financeiras.

Explique de forma curta, clara e objetiva por que a transação abaixo foi classificada como anômala.

Use apenas os dados fornecidos.
Não invente informações.
Não afirme que houve fraude confirmada.
Diga apenas que há indícios de comportamento suspeito.

Dados da transação:
- ID da transação: {transacao.id_transacao}
- Conta: {transacao.conta}
- Valor: R$ {transacao.valor}
- Tipo da transação: {transacao.tipo_transacao}
- Data: {transacao.data}
- Hora: {transacao.hora}
- Categoria: {transacao.categoria}
- Cidade: {transacao.cidade}
- Estado: {transacao.estado}
- Dispositivo: {transacao.dispositivo}
- Canal: {transacao.canal}
- Estabelecimento: {transacao.estabelecimento}
- Tentativas: {transacao.tentativas}

Resultado técnico da análise:
- ID da análise: {anomalia.id_analise}
- Score de risco: {anomalia.risco_score}
- Classificação: {anomalia.classificacao}
- Motivo técnico: {anomalia.motivo}

Responda em no máximo 5 linhas, exatamente neste formato:

1. Resumo:
2. Motivo da suspeita:
3. Risco:
4. Recomendação:
5. Explicação simples:
"""


def gerar_explicacao_anomalia(db: Session, anomalia_id: int) -> dict:
    anomalia = db_buscar_anomalia_por_id(db=db, anomalia_id=anomalia_id)

    prompt = montar_prompt_anomalia(anomalia)

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0.2,
            "num_predict": 180
        }
    }

    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        with httpx.Client(timeout=timeout) as client:
            resposta = client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload
            )

        resposta.raise_for_status()
        dados = resposta.json()

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível conectar ao Ollama. Verifique se o Ollama está aberto e rodando em http://localhost:11434."
        )

    except httpx.ReadTimeout:
        raise HTTPException(
            status_code=504,
            detail="A LLM demorou demais para responder. Tente novamente ou reduza o tamanho do prompt."
        )

    except httpx.HTTPStatusError as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar a LLM local: {erro.response.text}"
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao gerar explicação com LLM: {str(erro)}"
        )

    texto_llm = dados.get("response", "")

    texto_llm = texto_llm.replace("\\n", "\n")
    texto_llm = texto_llm.replace("\r\n", "\n")
    texto_llm = texto_llm.strip()

    explicacao_formatada = [
        linha.strip()
        for linha in texto_llm.split("\n")
        if linha.strip()
    ]

    return {
        "id_analise": anomalia.id_analise,
        "id_transacao": anomalia.id_transacao,
        "risco_score": anomalia.risco_score,
        "classificacao": anomalia.classificacao,
        "motivo_original": anomalia.motivo,
        "modelo_llm": OLLAMA_MODEL,
        "explicacao_llm": explicacao_formatada
    }