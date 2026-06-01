"""
Módulo: core/config.py
Descrição: Configurações centralizadas da aplicação.
           Limiares das regras de detecção, pesos de risco e
           regras padrão a serem inseridas no banco no startup.
Autor: Squad 4
Data: 2026
"""

import os

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./transacoes_db.db"

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
JSON_TREINO = os.path.join(DATA_DIR, "transacoes_treino.json")

# ---------------------------------------------------------------------------
# Limiares das regras de detecção
# ---------------------------------------------------------------------------
LIMIAR_HORA_INICIO    = 22     # Suspeito após 22h
LIMIAR_HORA_FIM       = 5      # Suspeito antes das 5h
LIMIAR_VALOR_NOTURNO  = 500.0  # Valor mínimo para suspeita noturna
LIMIAR_TENTATIVAS     = 2      # Nº mínimo de tentativas suspeitas
LIMIAR_MEDIA          = 3.0    # Múltiplo da média histórica

# Pesos de risco por tipo de regra (0–100)
PESOS_REGRA = {
    "horario":     40,
    "tentativas":  35,
    "valor_medio": 25,
}

# ---------------------------------------------------------------------------
# Regras padrão inseridas no banco na primeira execução
# ---------------------------------------------------------------------------
REGRAS_PADRAO = [
    {
        "nome": "Transação Noturna de Alto Valor",
        "descricao": (
            f"Transações acima de R$ {LIMIAR_VALOR_NOTURNO:.0f} realizadas "
            f"entre {LIMIAR_HORA_INICIO}h e {LIMIAR_HORA_FIM:02d}h."
        ),
        "tipo_regra": "horario",
        "ativa": True,
    },
    {
        "nome": "Múltiplas Tentativas",
        "descricao": (
            f"{LIMIAR_TENTATIVAS} ou mais tentativas na mesma operação "
            "indicam possível ataque de força bruta."
        ),
        "tipo_regra": "tentativas",
        "ativa": True,
    },
    {
        "nome": "Valor Atípico para a Conta",
        "descricao": (
            f"Valor superior a {LIMIAR_MEDIA:.0f}x "
            "a média histórica da conta do cliente."
        ),
        "tipo_regra": "valor_medio",
        "ativa": True,
    },
]
# ---------------------------------------------------------------------------
# Configurações da LLM
# ---------------------------------------------------------------------------

LLM_PROVIDER = "ollama"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:1b"