

import httpx
from google import genai
from fastapi import HTTPException
from sqlalchemy.orm import Session

from core.config import  GEMINI_API_KEY, GEMINI_MODEL
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
- Valor: R$ {transacao.valor}
- Tipo da transação: {transacao.tipo_transacao}
- Data: {transacao.data}
- Hora: {transacao.hora}
- Categoria: {transacao.categoria}
- Cidade: {transacao.cidade}
- Dispositivo: {transacao.dispositivo}
- Tentativas: {transacao.tentativas}

Resultado técnico:
- Score de risco: {anomalia.risco_score}
- Classificação: {anomalia.classificacao}
- Motivo técnico: {anomalia.motivo}

Responda em no máximo 4 linhas:
1. Resumo:
2. Motivo:
3. Risco:
4. Recomendação:
"""
def gerar_explicacao_anomalia(db: Session, anomalia_id: int) -> dict:
    anomalia = db_buscar_anomalia_por_id(db=db, anomalia_id=anomalia_id)
    prompt = montar_prompt_anomalia(anomalia)

    try:
        # 1. Cria o cliente usando a sintaxe da biblioteca NOVA
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 2. Faz a requisição para a IA
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        
        texto_llm = response.text

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro inesperado ao gerar explicação com Gemini: {str(erro)}"
        )

    # 3. Formatação da resposta para o JSON da API
    texto_llm = texto_llm.replace("\\n", "\n").replace("\r\n", "\n").strip()
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
        "modelo_llm": GEMINI_MODEL,
        "explicacao_llm": explicacao_formatada
    }

