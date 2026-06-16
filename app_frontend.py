import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# Ajuste global para evitar o erro de limite de células do Pandas Styler
pd.set_option("styler.render.max_elements", 999999)

API_BASE = "http://127.0.0.1:8000"
TIPO_TRANSACAO_OPCOES = ["pix", "transferencia", "debito", "credito", "boleto"]
CATEGORIA_OPCOES = ["transferencia", "lazer", "alimentacao", "saude", "shopping"]
CORES_BB = ["#0038A8", "#991B1B", "#FCE205", "#4B5563"]

# 1. Configuração da página institucional
st.set_page_config(page_title="Painel de Auditoria | Banco do Brasil", page_icon="🏦", layout="wide")

# 2. Injeção de CSS - Paleta de Cores Oficial do Banco do Brasil (Azul #0038A8 e Amarelo #FCE205)
st.markdown("""
    <style>
    .block-container { border-top: 10px solid #FCE205; padding-top: 1.5rem; }
    h1, h2, h3, h4, h5, h6 { color: #0038A8 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    [data-testid="stMetricValue"] { color: #0038A8 !important; font-weight: bold; font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"] { color: #4B5563 !important; font-weight: 500; }
    button[data-baseweb="tab"] { color: #6B7280; font-weight: 600; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0038A8 !important; border-bottom-color: #0038A8 !important; }
    div.stButton > button:first-child {
        background-color: #0038A8 !important; color: #FFFFFF !important;
        border: 1px solid #0038A8 !important; border-radius: 6px !important;
        padding: 0.5rem 2rem !important; font-weight: bold !important; transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #FCE205 !important; color: #0038A8 !important;
        border-color: #FCE205 !important; box-shadow: 0px 4px 10px rgba(0, 56, 168, 0.2);
    }
    .card-risco-alto { background: #FEF2F2; border-left: 5px solid #991B1B; padding: 1rem 1.25rem; border-radius: 6px; margin: 0.5rem 0; }
    .card-risco-medio { background: #FFFBEB; border-left: 5px solid #FCE205; padding: 1rem 1.25rem; border-radius: 6px; margin: 0.5rem 0; }
    .card-risco-baixo { background: #F0FDF4; border-left: 5px solid #16A34A; padding: 1rem 1.25rem; border-radius: 6px; margin: 0.5rem 0; }
    .card-risco-seguro { background: #EFF6FF; border-left: 5px solid #0038A8; padding: 1rem 1.25rem; border-radius: 6px; margin: 0.5rem 0; }
    </style>
""", unsafe_allow_html=True)

if "filtros_alertas" not in st.session_state:
    st.session_state.filtros_alertas = {
        "conta": "",
        "tipo_transacao": "",
        "categoria": "",
        "valor_minimo": None,
        "valor_maximo": None,
        "classificacao_risco": "",
        "motivo_alerta": "",
    }


def verificar_api() -> bool:
    try:
        requests.get(f"{API_BASE}/ping", timeout=3).raise_for_status()
        return True
    except requests.RequestException:
        return False


def api_get(endpoint: str, params: dict | None = None):
    """Busca dados na API — o front NÃO aplica regras de negócio, apenas consome."""
    response = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def resumir_motivo_alerta(motivo):
    """
    Resume o motivo detalhado vindo do backend (GET /anomalies) apenas para exibição visual.
    A decisão de fraude continua 100% no services/anomaly_detection.py.
    """
    if motivo is None or (isinstance(motivo, float) and pd.isna(motivo)):
        return "Transação Segura"

    texto = str(motivo).lower()
    rotulos = []

    if "noturna" in texto or "horário" in texto or "horario" in texto:
        rotulos.append("Horário Suspeito")
    if "tentativas" in texto:
        rotulos.append("Múltiplas Tentativas")
    if "atípico" in texto or "atipico" in texto or "excede" in texto or "média" in texto or "media" in texto:
        rotulos.append("Valor Atípico")
    if "anômalo" in texto or "anomalo" in texto or "isolation" in texto:
        rotulos.append("Padrão de Risco IA")

    return " + ".join(rotulos) if rotulos else "Alerta de Auditoria"


def extrair_categorias_individuais(motivo) -> list[str]:
    """Separa cada regra acionada — evita combinações ilegíveis no gráfico."""
    if motivo is None or (isinstance(motivo, float) and pd.isna(motivo)):
        return []

    texto = str(motivo).lower()
    categorias = []

    if "noturna" in texto or "horário" in texto or "horario" in texto:
        categorias.append("Horário Suspeito")
    if "tentativas" in texto:
        categorias.append("Múltiplas Tentativas")
    if "atípico" in texto or "atipico" in texto or "excede" in texto or "média" in texto or "media" in texto:
        categorias.append("Valor Atípico")
    if "anômalo" in texto or "anomalo" in texto or "isolation" in texto:
        categorias.append("Padrão de Risco IA")

    return categorias if categorias else ["Alerta de Auditoria"]


CORES_MOTIVO = {
    "Horário Suspeito": "#0038A8",
    "Múltiplas Tentativas": "#991B1B",
    "Valor Atípico": "#FCE205",
    "Padrão de Risco IA": "#4B5563",
    "Alerta de Auditoria": "#6B7280",
}


def preparar_distribuicao_alertas(df_alertas: pd.DataFrame) -> pd.DataFrame:
    """Conta cada tipo de regra separadamente (um alerta pode entrar em mais de uma barra)."""
    registros = []
    for motivo in df_alertas["motivo_real"]:
        for categoria in extrair_categorias_individuais(motivo):
            registros.append({"categoria": categoria})

    if not registros:
        return pd.DataFrame(columns=["categoria", "quantidade"])

    contagem = (
        pd.DataFrame(registros)
        .value_counts("categoria")
        .reset_index(name="quantidade")
    )
    return contagem.sort_values("quantidade", ascending=True)


def montar_params_transacoes(filtros: dict | None = None) -> dict:
    params = {}
    if not filtros:
        return params
    if filtros.get("conta"):
        params["conta"] = filtros["conta"]
    if filtros.get("tipo_transacao"):
        params["tipo_transacao"] = filtros["tipo_transacao"]
    if filtros.get("categoria"):
        params["categoria"] = filtros["categoria"]
    if filtros.get("valor_minimo") is not None:
        params["valor_minimo"] = filtros["valor_minimo"]
    if filtros.get("valor_maximo") is not None:
        params["valor_maximo"] = filtros["valor_maximo"]
    if filtros.get("is_fraude") is not None:
        params["is_fraude"] = filtros["is_fraude"]
    return params


def enriquecer_com_anomalias(transacoes: list, anomalias: list) -> pd.DataFrame:
    """Junta transações com anomalias da API — substitui o antigo definir_motivo() local."""
    df = pd.DataFrame(transacoes)
    if df.empty:
        return df

    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce")
    df["latitude_num"] = pd.to_numeric(df.get("latitude", pd.Series(dtype=float)), errors="coerce")
    df["longitude_num"] = pd.to_numeric(df.get("longitude", pd.Series(dtype=float)), errors="coerce")

    df_anom = pd.DataFrame(anomalias)
    if not df_anom.empty:
        df_anom = (
            df_anom.sort_values("risco_score", ascending=False)
            .drop_duplicates("id_transacao")
        )
        df = df.merge(
            df_anom[["id_transacao", "motivo", "risco_score", "classificacao", "data_analise"]],
            on="id_transacao",
            how="left",
        )
        df = df.rename(columns={
            "motivo": "motivo_real",
            "classificacao": "classificacao_risco",
            "data_analise": "data_analise_risco",
        })
    else:
        df["motivo_real"] = None
        df["risco_score"] = None
        df["classificacao_risco"] = None
        df["data_analise_risco"] = None

    df["motivo_alerta"] = df["motivo_real"].apply(resumir_motivo_alerta)
    df.loc[df["motivo_real"].isna(), "motivo_alerta"] = "Transação Segura"
    df["tem_alerta"] = df["motivo_real"].notna()
    return df


def carregar_dados_cache():
    transacoes = api_get("/transactions")
    anomalias = api_get("/anomalies")
    regras = api_get("/regras")
    df = enriquecer_com_anomalias(transacoes, anomalias)
    return df, pd.DataFrame(anomalias), pd.DataFrame(regras)


def carregar_transacoes_filtradas(filtros: dict) -> pd.DataFrame:
    params = montar_params_transacoes(filtros)
    transacoes = api_get("/transactions", params)
    anomalias = api_get("/anomalies")
    return enriquecer_com_anomalias(transacoes, anomalias)


def obter_dados_alertas(filtros: dict) -> pd.DataFrame:
    """
    1) Busca sempre as transações e anomalias atuais na API.
    2) Cruza com as anomalias do backend.
    3) Mantém só linhas com alerta e aplica filtros visuais (risco, motivo).
    """
    df_trabalho = carregar_transacoes_filtradas(filtros)
    df_alertas = df_trabalho[df_trabalho["tem_alerta"]].copy()

    if filtros.get("classificacao_risco"):
        df_alertas = df_alertas[df_alertas["classificacao_risco"] == filtros["classificacao_risco"]]

    if filtros.get("motivo_alerta"):
        df_alertas = df_alertas[df_alertas["motivo_alerta"].str.contains(filtros["motivo_alerta"], na=False)]

    return df_alertas.sort_values(by="data_hora", ascending=False)


def descrever_filtros_ativos(filtros: dict) -> str:
    partes = []
    if filtros.get("conta"):
        partes.append(f"Conta: {filtros['conta']}")
    if filtros.get("tipo_transacao"):
        partes.append(f"Tipo: {filtros['tipo_transacao']}")
    if filtros.get("categoria"):
        partes.append(f"Categoria: {filtros['categoria']}")
    if filtros.get("valor_minimo") is not None:
        partes.append(f"Valor mín.: R$ {filtros['valor_minimo']:.2f}")
    if filtros.get("valor_maximo") is not None:
        partes.append(f"Valor máx.: R$ {filtros['valor_maximo']:.2f}")
    if filtros.get("classificacao_risco"):
        partes.append(f"Risco: {filtros['classificacao_risco']}")
    if filtros.get("motivo_alerta"):
        partes.append(f"Motivo: {filtros['motivo_alerta']}")
    return " · ".join(partes) if partes else "Nenhum filtro aplicado — exibindo todos os alertas"


def buscar_anomalia_transacao(id_transacao: int):
    anomalias = api_get("/anomalies", {"id_transacao": id_transacao, "limit": 1})
    return anomalias[0] if anomalias else None


def exibir_resultado_validacao(anomalia: dict | None):
    if anomalia:
        score = anomalia.get("risco_score", "--")
        classificacao = anomalia.get("classificacao", "Não informada")
        motivo = anomalia.get("motivo", "Não informado")

        if classificacao == "Alto":
            classe = "card-risco-alto"
            icone = "🚨"
        elif classificacao == "Médio":
            classe = "card-risco-medio"
            icone = "⚠️"
        else:
            classe = "card-risco-baixo"
            icone = "ℹ️"

        st.markdown(
            f"""<div class="{classe}">
                <strong>{icone} Alerta emitido — Risco {classificacao}</strong><br>
                Score: <strong>{score}/100</strong><br>
                Motivo (backend): {motivo}<br>
                Resumo visual: <strong>{resumir_motivo_alerta(motivo)}</strong>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div class="card-risco-seguro">
                <strong>✅ Transação aprovada</strong><br>
                Nenhuma regra de fraude ou anomalia foi acionada pelo motor de detecção.
            </div>""",
            unsafe_allow_html=True,
        )


st.title("🏦 CAÇA ANOMALIAS")
st.markdown("### Painel Executivo de Auditoria e Análise de Anomalias")
st.divider()

try:
    with st.sidebar:
        st.markdown("### ⚙️ Painel de Controle")
        api_online = verificar_api()
        if api_online:
            st.success("🟢 API online")
        else:
            st.error("🔴 API offline")
        st.caption(f"Verificado às {datetime.now().strftime('%H:%M:%S')}")

        if st.button("🔄 Atualizar dados", use_container_width=True):
            st.experimental_rerun()

        with st.expander("📜 Regras de Negócio (resumo)"):
            try:
                for regra in api_get("/regras"):
                    icone = "✅" if regra["ativa"] else "⛔"
                    st.markdown(f"{icone} **{regra['nome']}**")
                    st.caption(regra["descricao"])
            except requests.RequestException:
                st.warning("Regras indisponíveis.")

    if not api_online:
        st.error("API offline. Execute: `python -m uvicorn main:app --reload`")
        st.stop()

    # 3. Carga de dados via API (sem SQLite, sem regras locais)
    df, df_anomalias_api, df_regras = carregar_dados_cache()

    if df.empty:
        st.warning("Nenhuma transação encontrada na API.")
        st.stop()

    # 4. Métricas financeiras e operacionais
    total_transacoes = len(df)
    total_anomalias = int(df["tem_alerta"].sum())
    taxa_fraude = (total_anomalias / total_transacoes) * 100 if total_transacoes > 0 else 0
    volume_total = df["valor"].sum()
    df_falsos_negativos = df[(df["is_fraude"] == True) & (~df["tem_alerta"])]
    df_alertas_sem_rotulo = df[(df["is_fraude"] == False) & (df["tem_alerta"])]

    # 5. Cards de métricas
    st.markdown("### 📊 Visão Geral")
    st.markdown(
        '<div style="background:#f8fafc; padding:16px 20px; border-radius:16px; box-shadow:0 10px 25px rgba(0,0,0,0.06); margin-bottom:16px;">',
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Volume Total Analisado", f"R$ {volume_total:,.2f}")
    with col2:
        st.metric("Transações Processadas", f"{total_transacoes:,}")
    with col3:
        st.metric(
            "Alertas da Auditoria ⚠️", total_anomalias,
            delta=f"{taxa_fraude:.2f}% do volume", delta_color="inverse",
        )
    with col4:
        st.metric("Falsos Negativos", len(df_falsos_negativos), delta="dataset vs motor", delta_color="off")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Abas de análise
    aba_graficos, aba_fraudes, aba_tabela, aba_regras, aba_formulario = st.tabs([
        "📊 Visão Geral",
        "⚠️ Alertas e Risco Operacional",
        "📋 Histórico Completo",
        "📜 Regras de Negócio",
        "➕ Simular Transação (PIX/TED)",
    ])

    with aba_graficos:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_volume = df.groupby(df["data_hora"].dt.date)["valor"].sum().reset_index()
            df_volume.columns = ["Data", "Volume Financeiro (R$)"]
            fig_volume = px.line(
                df_volume, x="Data", y="Volume Financeiro (R$)",
                title="Evolução do Volume Transacionado Diário",
                color_discrete_sequence=["#0038A8"],
            )
            fig_volume.update_traces(fill="tozeroy", fillcolor="rgba(252, 226, 5, 0.15)")
            fig_volume.update_layout(plot_bgcolor="white", xaxis_title="Período de Análise", yaxis_title="Volume (R$)")
            st.plotly_chart(fig_volume, use_container_width=True)

        with col_g2:
            df_alertas = df[df["tem_alerta"]].copy()
            if not df_alertas.empty:
                df_alertas["dia"] = df_alertas["data_hora"].dt.date
                df_evolucao = df_alertas.groupby("dia").size().reset_index(name="Alertas")
                df_evolucao.columns = ["Data", "Alertas"]
                fig_alertas = px.bar(
                    df_evolucao, x="Data", y="Alertas",
                    title="Evolução Diária de Alertas Emitidos",
                    color_discrete_sequence=["#991B1B"],
                )
                fig_alertas.update_layout(plot_bgcolor="white")
                st.plotly_chart(fig_alertas, use_container_width=True)
            else:
                st.info("Sem alertas para exibir evolução diária.")

        st.write("#### Comparativo por Canal de Pagamento")
        df_canal = df.groupby("tipo_transacao").agg(
            transacoes=("id_transacao", "count"),
            alertas=("tem_alerta", "sum"),
        ).reset_index()
        fig_canal = px.bar(
            df_canal, x="tipo_transacao", y=["transacoes", "alertas"],
            title="Transações vs Alertas por Modalidade",
            barmode="group", color_discrete_sequence=["#0038A8", "#FCE205"],
        )
        fig_canal.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig_canal, use_container_width=True)

    with aba_fraudes:
        st.write("### 🚨 Detalhamento das Anomalias e Falsos Negativos")

        st.info(
            "**Como os filtros funcionam:**\n\n"
            "1. Você escolhe os critérios abaixo e clica em **Buscar alertas**.\n"
            "2. O painel chama a API (`GET /transactions`) com conta, tipo, categoria e valor.\n"
            "3. O resultado é cruzado com os alertas reais do backend (`GET /anomalies`).\n"
            "4. Os gráficos, mapa e tabela desta aba mostram **somente** os alertas filtrados.\n\n"
            "Os filtros **Risco** e **Natureza do alerta** refinam a visualização na tela, "
            "sem nova chamada à API."
        )

        filtros = st.session_state.filtros_alertas
        st.markdown("#### 🔎 Filtrar alertas")

        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            inp_conta = st.text_input("Conta corrente", value=filtros["conta"], placeholder="Ex: 45678-9", key="alerta_conta")
        with col_f2:
            opcoes_tipo = ["Todos"] + TIPO_TRANSACAO_OPCOES
            idx_tipo = opcoes_tipo.index(filtros["tipo_transacao"]) if filtros["tipo_transacao"] in opcoes_tipo else 0
            inp_tipo = st.selectbox("Tipo de pagamento", opcoes_tipo, index=idx_tipo, key="alerta_tipo")
        with col_f3:
            opcoes_cat = ["Todos"] + CATEGORIA_OPCOES
            idx_cat = opcoes_cat.index(filtros["categoria"]) if filtros["categoria"] in opcoes_cat else 0
            inp_categoria = st.selectbox("Categoria", opcoes_cat, index=idx_cat, key="alerta_categoria")
        with col_f4:
            opcoes_risco = ["Todos", "Alto", "Médio", "Baixo"]
            idx_risco = opcoes_risco.index(filtros["classificacao_risco"]) if filtros["classificacao_risco"] in opcoes_risco else 0
            inp_risco = st.selectbox("Classificação de risco", opcoes_risco, index=idx_risco, key="alerta_risco")

        col_f5, col_f6, col_f7, col_f8 = st.columns(4)
        with col_f5:
            inp_valor_min = st.number_input("Valor mínimo (R$)", min_value=0.0, step=50.0, value=float(filtros["valor_minimo"] or 0.0), key="alerta_vmin")
        with col_f6:
            inp_valor_max = st.number_input("Valor máximo (R$)", min_value=0.0, step=50.0, value=float(filtros["valor_maximo"] or 0.0), key="alerta_vmax")
        with col_f7:
            opcoes_motivo = ["Todos", "Horário Suspeito", "Múltiplas Tentativas", "Valor Atípico", "Padrão de Risco IA", "Alerta de Auditoria"]
            idx_motivo = opcoes_motivo.index(filtros["motivo_alerta"]) if filtros["motivo_alerta"] in opcoes_motivo else 0
            inp_motivo = st.selectbox("Natureza do alerta", opcoes_motivo, index=idx_motivo, key="alerta_motivo")
        with col_f8:
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                buscar_alertas = st.button("Buscar alertas", use_container_width=True, key="btn_buscar_alertas")
            with col_btn2:
                limpar_alertas = st.button("Limpar", use_container_width=True, key="btn_limpar_alertas")

        if buscar_alertas:
            st.session_state.filtros_alertas = {
                "conta": inp_conta.strip(),
                "tipo_transacao": "" if inp_tipo == "Todos" else inp_tipo,
                "categoria": "" if inp_categoria == "Todos" else inp_categoria,
                "valor_minimo": inp_valor_min if inp_valor_min > 0 else None,
                "valor_maximo": inp_valor_max if inp_valor_max > 0 else None,
                "classificacao_risco": "" if inp_risco == "Todos" else inp_risco,
                "motivo_alerta": "" if inp_motivo == "Todos" else inp_motivo,
            }

        if limpar_alertas:
            st.session_state.filtros_alertas = {
                "conta": "", "tipo_transacao": "", "categoria": "",
                "valor_minimo": None, "valor_maximo": None,
                "classificacao_risco": "", "motivo_alerta": "",
            }
            st.experimental_rerun()

        st.caption(f"**Filtros ativos:** {descrever_filtros_ativos(st.session_state.filtros_alertas)}")

        df_motivos = obter_dados_alertas(st.session_state.filtros_alertas)
        total_alertas_filtrados = len(df_motivos)
        st.metric("Alertas encontrados com os filtros", total_alertas_filtrados)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Falsos Negativos (base geral)", len(df_falsos_negativos))
        with col_m2:
            st.metric("Alertas sem Rótulo (base geral)", len(df_alertas_sem_rotulo))

        if len(df_falsos_negativos) > 0 or len(df_alertas_sem_rotulo) > 0:
            with st.expander("🔍 Ver divergências Dataset vs Motor (sem filtro)", expanded=False):
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("**Falsos negativos** — fraude no dataset, sem alerta da API")
                    if len(df_falsos_negativos) > 0:
                        st.dataframe(
                            df_falsos_negativos[
                                ["data_hora", "conta", "tipo_transacao", "valor", "localizacao", "is_fraude"]
                            ].head(100),
                            use_container_width=True,
                        )
                    else:
                        st.success("Nenhum falso negativo.")
                with col_d2:
                    st.markdown("**Alertas sem rótulo** — motor detectou, dataset normal")
                    if len(df_alertas_sem_rotulo) > 0:
                        st.dataframe(
                            df_alertas_sem_rotulo[
                                ["data_hora", "conta", "tipo_transacao", "valor", "risco_score", "classificacao_risco", "motivo_alerta"]
                            ].head(100),
                            use_container_width=True,
                        )
                    else:
                        st.success("Nenhum alerta divergente.")

        st.divider()

        if total_alertas_filtrados > 0:

            col_grafico1, col_grafico2 = st.columns(2)
            with col_grafico1:
                df_distribuicao = preparar_distribuicao_alertas(df_motivos)
                total_ocorrencias = int(df_distribuicao["quantidade"].sum())

                fig_motivos = px.pie(
                    df_distribuicao,
                    names="categoria",
                    values="quantidade",
                    title="Distribuição por Natureza de Alerta",
                    hole=0.4,
                    color="categoria",
                    color_discrete_map=CORES_MOTIVO,
                )
                fig_motivos.update_traces(
                    texttemplate="%{label}<br>%{value} (%{percent})",
                    textposition="outside",
                    textinfo="none",
                    outsidetextfont=dict(size=12),
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Quantidade: %{value}<br>"
                        "Participação: %{percent}<extra></extra>"
                    ),
                    pull=[0.03] * len(df_distribuicao),
                )
                fig_motivos.update_layout(
                    plot_bgcolor="white",
                    height=400,
                    margin=dict(l=20, r=160, t=50, b=20),
                    showlegend=True,
                    legend=dict(
                        title="Tipos de regra",
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02,
                        font=dict(size=12),
                    ),
                )
                st.caption(
                    f"**{total_ocorrencias}** ocorrências de regras em **{total_alertas_filtrados}** alertas. "
                    "Um alerta pode acionar mais de uma regra."
                )
                st.plotly_chart(fig_motivos, use_container_width=True)
            with col_grafico2:
                df_canal_alertas = (
                    df_motivos.groupby("tipo_transacao", as_index=False)
                    .size()
                    .rename(columns={"size": "quantidade"})
                    .sort_values("quantidade", ascending=False)
                )
                fig_tipos = px.bar(
                    df_canal_alertas,
                    x="tipo_transacao",
                    y="quantidade",
                    title="Volumetria de Alertas por Canal de Pagamento",
                    color_discrete_sequence=["#0038A8"],
                    text="quantidade",
                )
                fig_tipos.update_layout(
                    plot_bgcolor="white",
                    xaxis_title="Canal de pagamento",
                    yaxis_title="Quantidade de alertas",
                )
                fig_tipos.update_traces(textposition="outside")
                st.plotly_chart(fig_tipos, use_container_width=True)

            st.write("#### 🗺️ Mapa Geográfico de Alertas")
            df_mapa = df_motivos.dropna(subset=["latitude_num", "longitude_num"])
            if not df_mapa.empty:
                fig_mapa = px.scatter_geo(
                    df_mapa, lat="latitude_num", lon="longitude_num",
                    hover_name="cidade",
                    hover_data=["conta", "valor", "classificacao_risco", "motivo_alerta"],
                    color="classificacao_risco",
                    title="Distribuição Geográfica dos Alertas",
                    color_discrete_map={"Alto": "#991B1B", "Médio": "#FCE205", "Baixo": "#0038A8"},
                    scope="south america",
                )
                fig_mapa.update_layout(geo=dict(landcolor="#F8FAFC", countrycolor="#CBD5E1"))
                st.plotly_chart(fig_mapa, use_container_width=True)
            else:
                st.info("Sem coordenadas válidas para exibir o mapa.")

            st.write("#### 📝 Registro de Auditoria (Últimas Ocorrências)")
            colunas_analise = [
                "data_analise_risco", "data_hora", "conta", "tipo_transacao", "valor",
                "localizacao", "dispositivo", "risco_score", "classificacao_risco", "motivo_alerta",
            ]
            df_exibicao_fraudes = (
                df_motivos[colunas_analise]
                .sort_values(by="data_analise_risco", ascending=False)
                .head(500)
            )
            st.dataframe(df_exibicao_fraudes, use_container_width=True)

            with st.expander("📚 Motivo completo retornado pelo backend"):
                st.dataframe(
                    df_motivos[["data_analise_risco", "data_hora", "conta", "motivo_real", "risco_score", "classificacao_risco"]]
                    .sort_values(by="data_analise_risco", ascending=False).head(100),
                    use_container_width=True,
                )

            st.download_button(
                "📥 Exportar Alertas (CSV)",
                df_exibicao_fraudes.to_csv(index=False).encode("utf-8"),
                file_name=f"alertas_auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.warning("Nenhum alerta encontrado com os filtros atuais. Tente limpar os filtros ou ampliar os critérios.")

    with aba_tabela:
        st.write("#### Últimas Transações Registradas (Base Geral)")
        df_exibicao = df.tail(1000)
        st.caption(f"Exibindo as últimas {len(df_exibicao):,} transações. Use a aba **Alertas** para filtrar por risco.")

        def destacar_anomalias(row):
            return [
                "background-color: #FFFBEB; color: #991B1B; font-weight: 500"
                if row.tem_alerta else ""
                for _ in row
            ]

        st.dataframe(df_exibicao.style.apply(destacar_anomalias, axis=1), use_container_width=True)
        st.download_button(
            "📥 Exportar Histórico (CSV)",
            df_exibicao.to_csv(index=False).encode("utf-8"),
            file_name=f"historico_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    with aba_regras:
        st.write("### 📜 Regras de Negócio do Motor de Detecção")
        st.caption(
            "Estas regras são cadastradas no banco (`regras_fraude`) e executadas pelo "
            "`services/anomaly_detection.py`. O front apenas consulta via `GET /regras`."
        )
        if df_regras.empty:
            st.info("Nenhuma regra retornada pela API.")
        else:
            for _, regra in df_regras.iterrows():
                status = "✅ Ativa" if regra["ativa"] else "⛔ Inativa"
                st.markdown(f"**{regra['nome']}** — {status}")
                st.write(regra["descricao"])
                st.caption(f"Tipo: `{regra['tipo_regra']}` · ID: `{regra['id_regra']}`")
                st.divider()
            st.dataframe(df_regras, use_container_width=True)

    with aba_formulario:
        st.write("### 📥 Simulador de Injeção de Transações em Tempo Real")
        st.write("Preencha as variáveis regulatórias para simular o comportamento transacional do cliente.")

        with st.form("form_nova_transacao", clear_on_submit=False):
            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:
                st.markdown("##### 👤 Dados da Conta e Valores")
                conta = st.text_input("Número da Conta Corrente", value="45678-9", placeholder="Ex: 12345-6")
                valor = st.number_input("Valor Nominal da Operação (R$)", min_value=0.01, step=50.0, value=150.0)
                tipo_transacao = st.selectbox("Modalidade de Pagamento", TIPO_TRANSACAO_OPCOES)
                categoria = st.selectbox("Categoria de Destino", CATEGORIA_OPCOES)
                estabelecimento = st.text_input("Nome do Beneficiário / Favorecido", value="Banco do Brasil S.A.")

            with col_f2:
                st.markdown("##### 📱 Canal de Acesso e Segurança")
                canal = st.selectbox("Canal de Origem", ["app_mobile", "web", "caixa_eletronico", "presencial"])
                dispositivo = st.selectbox("Dispositivo Autenticado", ["app_mobile", "web", "caixa_eletronico"])
                tentativas = st.number_input("Tentativas de Validação de Senha", min_value=1, max_value=10, value=1)
                ip_origem = st.text_input("Endereço IP de Conexão", value="192.168.0.1")
                descricao = st.text_area(
                    "Metadados / Histórico do Log",
                    value="Simulação efetuada para fins de homologação e compliance.",
                    max_chars=150,
                )

            with col_f3:
                st.markdown("##### 📍 Dados de Telecomunicações / GPS")
                cidade = st.text_input("Município da Operação", value="Brasilia")
                estado = st.text_input("Unidade Federativa (UF)", value="DF", max_chars=2)
                pais = st.text_input("País de Origem", value="Brasil")
                latitude_input = st.text_input("Coordenada: Latitude", value="-15.793889")
                longitude_input = st.text_input("Coordenada: Longitude", value="-47.882778")

            st.markdown("<br>", unsafe_allow_html=True)
            botao_enviar = st.form_submit_button("🚀 Enviar para Validação do Modelo")

            if botao_enviar:
                if not conta or not cidade or not estado:
                    st.error("❌ Os campos Conta Corrente, Município e Unidade Federativa são obrigatórios!")
                else:
                    agora = datetime.now()
                    payload = {
                        "conta": str(conta),
                        "valor": float(valor),
                        "tipo_transacao": str(tipo_transacao),
                        "localizacao": f"{cidade}, {estado}, {pais}",
                        "dispositivo": str(dispositivo),
                        "canal": str(canal),
                        "descricao": str(descricao),
                        "data": agora.strftime("%Y-%m-%d"),
                        "hora": agora.strftime("%H:%M:%S"),
                        "dia_semana": agora.strftime("%A"),
                        "categoria": str(categoria),
                        "cidade": str(cidade),
                        "estado": str(estado),
                        "pais": str(pais),
                        "latitude": str(latitude_input),
                        "longitude": str(longitude_input),
                        "estabelecimento": str(estabelecimento),
                        "tentativas": int(tentativas),
                        "ip_origem": str(ip_origem),
                    }

                    try:
                        with st.spinner("Conectando à API de Prevenção a Fraudes..."):
                            response = requests.post(f"{API_BASE}/transactions/", json=payload, timeout=10)

                        if response.status_code in [200, 201]:
                            resultado = response.json()
                            st.success("✅ Operação transmitida! O banco de dados consolidou o registro com sucesso.")
                            anomalia = buscar_anomalia_transacao(resultado["id_transacao"])
                            exibir_resultado_validacao(anomalia)
                            st.session_state.filtros_alertas = {
                                "conta": "", "tipo_transacao": "", "categoria": "",
                                "valor_minimo": None, "valor_maximo": None,
                                "classificacao_risco": "", "motivo_alerta": "",
                            }
                            st.experimental_rerun()
                            if anomalia:
                                st.balloons()
                        else:
                            st.error(f"❌ Falha no Contrato de Dados (Erro {response.status_code})")
                            st.code(response.text, language="json")

                    except requests.exceptions.ConnectionError:
                        st.error("API offline. Execute: python -m uvicorn main:app --reload")
                    except Exception as err:
                        st.error(f"Erro ao enviar transação: {err}")

except requests.exceptions.ConnectionError:
    st.error(
        "Não foi possível conectar à API. Inicie o backend com "
        "`python -m uvicorn main:app --reload` e depois `streamlit run app_frontend.py`."
    )
except Exception as e:
    st.error(f"Erro crítico no carregamento dos módulos do dashboard: {e}")
