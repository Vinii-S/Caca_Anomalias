import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# Ajuste global para evitar o erro de limite de células do Pandas Styler
pd.set_option("styler.render.max_elements", 999999)

# 1. Configuração da página institucional
st.set_page_config(page_title="Painel de Auditoria | Banco do Brasil", page_icon="🏦", layout="wide")

# 2. Injeção de CSS - Palheta de Cores Oficial do Banco do Brasil (Azul #0038A8 e Amarelo #FCE205)
st.markdown("""
    <style>
    /* Faixa superior Amarela BB */
    .block-container { border-top: 10px solid #FCE205; padding-top: 1.5rem; }
    
    /* Customização de Títulos */
    h1, h2, h3, h4, h5, h6 { color: #0038A8 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Customização dos Cards de Métrica */
    [data-testid="stMetricValue"] { color: #0038A8 !important; font-weight: bold; font-size: 2.2rem; }
    [data-testid="stMetricLabel"] { color: #4B5563 !important; font-weight: 500; }
    
    /* Estilização Premium das Abas (Tabs) */
    button[data-baseweb="tab"] { color: #6B7280; font-weight: 600; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #0038A8 !important; border-bottom-color: #0038A8 !important; }
    
    /* Estilização do Botão Principal do Formulário (Padrão Corporativo BB) */
    div.stButton > button:first-child {
        background-color: #0038A8 !important;
        color: #FFFFFF !important;
        border: 1px solid #0038A8 !important;
        border-radius: 6px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #FCE205 !important;
        color: #0038A8 !important;
        border-color: #FCE205 !important;
        box-shadow: 0px 4px 10px rgba(0, 56, 168, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Sistema de Prevenção a Fraudes")
st.markdown("### Painel Executivo de Auditoria e Análise de Anomalias")
st.divider()

# 3. Conexão e Carga de Dados
def carregar_dados():
    conn = sqlite3.connect("transacoes_db.db")
    df = pd.read_sql_query("SELECT * FROM transacoes", conn)
    conn.close()
    
    df['data_hora'] = pd.to_datetime(df['data_hora'])
    
    # Motor de Regras Visuais para explicar o risco
    def definir_motivo(row):
        if row['is_fraude'] == 0:
            return "Transação Segura"
        motivos = []
        if pd.notna(row['hora']) and ('00:00' <= str(row['hora']) <= '06:00'):
            motivos.append("Horário Suspeito")
        if row['valor'] > 5000:
            motivos.append("Valor Atípico")
        if pd.notna(row.get('tentativas')) and row['tentativas'] > 2:
            motivos.append("Múltiplas Tentativas")
        if not motivos:
            # 🔄 Atualizado de 'Padrão de Risco IA' para 'Falso negativo'
            motivos.append("Falso negativo")
        return " + ".join(motivos)

    df['motivo_alerta'] = df.apply(definir_motivo, axis=1)
    return df

try:
    # Carga limpa dos dados estruturados
    df = carregar_dados()
    
    # 4. Cálculos estatísticos de Métricas Financeiras
    total_transacoes = len(df)
    df_fraudes = df[df['is_fraude'] == 1]
    total_anomalias = len(df_fraudes)
    taxa_fraude = (total_anomalias / total_transacoes) * 100 if total_transacoes > 0 else 0
    volume_total = df['valor'].sum()

    # 5. Cards de Métricas Estilizados (Layout Horizontal)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Total Analisado", value=f"R$ {volume_total:,.2f}")
    with col2:
        st.metric(label="Total de Transações Processadas", value=f"{total_transacoes:,}")
    with col3:
        st.metric(label="Alertas Emitidos pela Auditoria ⚠️", value=total_anomalias, delta=f"{taxa_fraude:.2f}% de volumetria", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Organização das Abas de Análise
    aba_graficos, aba_fraudes, aba_tabela, aba_formulario = st.tabs([
        "📊 Visão Geral", 
        "⚠️ Alertas e Risco Operacional", 
        "📋 Histórico Completo",
        "➕ Simular Transação (PIX/TED)"
    ])

    with aba_graficos:
        df_agrupado = df.groupby(df['data_hora'].dt.date)['valor'].sum().reset_index()
        df_agrupado.columns = ['Data', 'Volume Financeiro (R$)']
        
        # Gráfico de Linha nas Cores Corporativas do BB
        fig = px.line(df_agrupado, x="Data", y="Volume Financeiro (R$)", 
                      title="Evolução do Volume Transacionado Diário", color_discrete_sequence=["#0038A8"])
        fig.update_traces(fill='tozeroy', fillcolor='rgba(252, 226, 5, 0.15)') 
        fig.update_layout(plot_bgcolor="white", xaxis_title="Período de Análise", yaxis_title="Volume (R$)")
        st.plotly_chart(fig, use_container_width=True)

    with aba_fraudes:
        st.write("### 🚨 Detalhamento das Anomalias e Falsos Negativos")
        if total_anomalias > 0:
            col_grafico1, col_grafico2 = st.columns(2)
            with col_grafico1:
                # Palheta Customizada usando tons profissionais de Alerta e Identidade BB
                fig_motivos = px.pie(df_fraudes, names='motivo_alerta', title='Distribuição por Natureza de Alerta',
                                     hole=0.4, color_discrete_sequence=["#0038A8", "#991B1B", "#FCE205", "#4B5563"])
                st.plotly_chart(fig_motivos, use_container_width=True)
            with col_grafico2:
                fig_tipos = px.bar(df_fraudes, x='tipo_transacao', title='Volumetria de Alertas por Canal de Pagamento', color_discrete_sequence=["#0038A8"])
                fig_tipos.update_layout(plot_bgcolor="white")
                st.plotly_chart(fig_tipos, use_container_width=True)

            st.write("#### 📝 Registro de Auditoria (Últimas Ocorrências)")
            colunas_analise = ['data_hora', 'conta', 'tipo_transacao', 'valor', 'localizacao', 'dispositivo', 'motivo_alerta']
            df_exibicao_fraudes = df_fraudes[colunas_analise].sort_values(by='data_hora', ascending=False).head(500)
            st.dataframe(df_exibicao_fraudes, use_container_width=True)
        else:
            st.success("Nenhuma anomalia detectada no lote de dados atual! 🎉")

    with aba_tabela:
        st.write("#### Últimas 1.000 Transações Registradas (Base Geral)")
        df_exibicao = df.tail(1000)
        def destacar_anomalias(row):
            # Mantém destaque suave para linhas de auditoria sinalizadas
            return ['background-color: #FFFBEB; color: #991B1B; font-weight: 500' if row.is_fraude == 1 else '' for _ in row]
        st.dataframe(df_exibicao.style.apply(destacar_anomalias, axis=1), use_container_width=True)

    with aba_formulario:
        st.write("### 📥 Simulador de Injeção de Transações em Tempo Real")
        st.write("Preencha as variáveis regulatórias para simular o comportamento transacional do cliente.")
        
        with st.form("form_nova_transacao", clear_on_submit=False):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                st.markdown("##### 👤 Dados da Conta e Valores")
                conta = st.text_input("Número da Conta Corrente", value="45678-9", placeholder="Ex: 12345-6")
                valor = st.number_input("Valor Nominal da Operação (R$)", min_value=0.01, step=50.0, value=150.0)
                tipo_transacao = st.selectbox("Modalidade de Pagamento", ["pix", "transferencia", "debito", "boleto"])
                categoria = st.selectbox("Categoria de Destino", ["transferencia", "lazer", "alimentacao", "saude", "shopping"])
                estabelecimento = st.text_input("Nome do Beneficiário / Favorecido", value="Banco do Brasil S.A.")

            with col_f2:
                st.markdown("##### 📱 Canal de Acesso e Segurança")
                canal = st.selectbox("Canal de Origem", ["app_mobile", "web", "caixa_eletronico", "presencial"])
                dispositivo = st.selectbox("Dispositivo Autenticado", ["app_mobile", "web", "caixa_eletronico"])
                tentativas = st.number_input("Tentativas de Validação de Senha", min_value=1, max_value=10, value=1)
                ip_origem = st.text_input("Endereço IP de Conexão", value="192.168.0.1")
                descricao = st.text_area("Metadados / Histórico do Log", value="Simulação efetuada para fins de homologação e compliance.", max_chars=150)

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
                    
                    # Contrato estrito com o Pydantic do backend
                    payload = {
                        "conta": str(conta),
                        "valor": float(valor),
                        "tipo_transacao": str(tipo_transacao),
                        "data_hora": agora.strftime("%Y-%m-%d %H:%M:%S.000000"),
                        "localizacao": f"{cidade}, {estado}, {pais}",
                        "dispositivo": str(dispositivo),
                        "canal": str(canal),
                        "descricao": str(descricao),
                        "data": agora.strftime("%Y-%m-%d"),
                        "hora": agora.strftime("%H:%M"),
                        "dia_semana": agora.strftime("%A"),  
                        "categoria": str(categoria),
                        "cidade": str(cidade),
                        "estado": str(estado),
                        "pais": str(pais),
                        "latitude": str(latitude_input),   
                        "longitude": str(longitude_input), 
                        "estabelecimento": str(estabelecimento),
                        "tentativas": int(tentativas),
                        "ip_origem": str(ip_origem)
                    }
                    
                    try:
                        url_api = "http://127.0.0.1:8000/transactions/" 
                        
                        with st.spinner("Conectando à API de Prevenção a Fraudes..."):
                            response = requests.post(url_api, json=payload)
                        
                        if response.status_code in [200, 201]:
                            st.success("✅ Operação transmitida! O banco de dados consolidou o registro com sucesso.")
                            st.balloons()
                        else:
                            st.error(f"❌ Falha no Contrato de Dados (Erro {response.status_code})")
                            st.code(response.text, language="json")
                            
                    except Exception as err:
                        st.error(f"Não foi possível estabelecer conexão com o endpoint da API: {err}")

except Exception as e:
    st.error(f"Erro crítico no carregamento dos módulos do dashboard: {e}") 