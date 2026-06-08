import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import requests
from datetime import datetime

# Ajuste global para evitar o erro de limite de células do Pandas Styler
pd.set_option("styler.render.max_elements", 999999)

# 1. Configuração da página
st.set_page_config(page_title="Monitoramento | BB", page_icon="🏦", layout="wide")

# 2. Injeção de CSS (Identidade BB)
st.markdown("""
    <style>
    .block-container { border-top: 8px solid #FCE205; padding-top: 2rem; }
    h1, h2, h3 { color: #0038A8 !important; }
    [data-testid="stMetricValue"] { color: #0038A8; }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Sistema de Prevenção a Fraudes")
st.markdown("**Monitoramento Transacional e Detecção de Anomalias**")
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
            motivos.append("Padrão de Risco IA")
        return " + ".join(motivos)

    df['motivo_alerta'] = df.apply(definir_motivo, axis=1)
    return df

try:
    # 💥 Linha 50 corrigida: Agora todo o bloco abaixo está indentado corretamente com TAB
    df = carregar_dados()
    
    # 4. Cálculos de Métricas
    total_transacoes = len(df)
    df_fraudes = df[df['is_fraude'] == 1]
    total_anomalias = len(df_fraudes)
    taxa_fraude = (total_anomalias / total_transacoes) * 100 if total_transacoes > 0 else 0
    volume_total = df['valor'].sum()

    # 5. Cards de Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume Total Analisado", value=f"R$ {volume_total:,.2f}")
    with col2:
        st.metric(label="Total de Transações", value=f"{total_transacoes:,}")
    with col3:
        st.metric(label="Alertas de Fraude ⚠️", value=total_anomalias, delta=f"{taxa_fraude:.2f}% de risco", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Organização em Abas
    aba_graficos, aba_fraudes, aba_tabela, aba_formulario = st.tabs([
        "📊 Visão Geral", 
        "⚠️ Alertas e Motivos (Análise de Risco)", 
        "📋 Histórico Completo",
        "➕ Simular Transação (PIX/TED)"
    ])

    with aba_graficos:
        df_agrupado = df.groupby(df['data_hora'].dt.date)['valor'].sum().reset_index()
        df_agrupado.columns = ['Data', 'Volume Financeiro (R$)']
        
        fig = px.line(df_agrupado, x="Data", y="Volume Financeiro (R$)", 
                      title="Evolução do Volume Transacionado", color_discrete_sequence=["#0038A8"])
        fig.update_traces(fill='tozeroy', fillcolor='rgba(252, 226, 5, 0.2)') 
        fig.update_layout(plot_bgcolor="white", xaxis_title="", yaxis_title="R$")
        st.plotly_chart(fig, use_container_width=True)

    with aba_fraudes:
        st.write("### 🚨 Detalhamento das Anomalias Detectadas")
        if total_anomalias > 0:
            col_grafico1, col_grafico2 = st.columns(2)
            with col_grafico1:
                fig_motivos = px.pie(df_fraudes, names='motivo_alerta', title='Distribuição dos Motivos de Alerta',
                                     hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
                st.plotly_chart(fig_motivos, use_container_width=True)
            with col_grafico2:
                fig_tipos = px.bar(df_fraudes, x='tipo_transacao', title='Fraudes por Tipo de Transação', color_discrete_sequence=["#991B1B"])
                st.plotly_chart(fig_tipos, use_container_width=True)

            st.write("#### 📝 Registro de Alertas")
            colunas_analise = ['data_hora', 'conta', 'tipo_transacao', 'valor', 'localizacao', 'dispositivo', 'motivo_alerta']
            df_exibicao_fraudes = df_fraudes[colunas_analise].sort_values(by='data_hora', ascending=False).head(500)
            st.dataframe(df_exibicao_fraudes, use_container_width=True)
        else:
            st.success("Nenhuma fraude detectada neste lote de dados! 🎉")

    with aba_tabela:
        st.write("#### Últimas 1.000 Transações Registradas (Geral)")
        df_exibicao = df.tail(1000)
        def destacar_anomalias(row):
            return ['background-color: #FEE2E2; color: #991B1B' if row.is_fraude == 1 else '' for _ in row]
        st.dataframe(df_exibicao.style.apply(destacar_anomalias, axis=1), use_container_width=True)

    with aba_formulario:
        st.write("### 📥 Simulador de Injeção de Transações em Tempo Real")
        st.write("Ajuste as variáveis abaixo para testar a resiliência e a resposta do modelo Isolation Forest.")
        
        with st.form("form_nova_transacao", clear_on_submit=False):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                st.markdown("##### 👤 Dados da Conta e Valores")
                conta = st.text_input("Número da Conta", value="45678-9", placeholder="Ex: 12345-6")
                valor = st.number_input("Valor da Transação (R$)", min_value=0.01, step=50.0, value=150.0)
                tipo_transacao = st.selectbox("Tipo de Transação", ["pix", "transferencia", "debito", "boleto"])
                categoria = st.selectbox("Categoria do Gasto", ["transferencia", "lazer", "alimentacao", "saude", "shopping"])
                estabelecimento = st.text_input("Estabelecimento / Beneficiário", value="Banco do Brasil S.A.")

            with col_f2:
                st.markdown("##### 📱 Canal e Segurança")
                canal = st.selectbox("Canal de Atendimento", ["app_mobile", "web", "caixa_eletronico", "presencial"])
                dispositivo = st.selectbox("Dispositivo Usado", ["app_mobile", "web", "caixa_eletronico"])
                tentativas = st.number_input("Número de Tentativas de Senha", min_value=1, max_value=10, value=1)
                ip_origem = st.text_input("IP de Origem", value="192.168.0.1")
                descricao = st.text_area("Descrição da Transação", value="Transação simulada via Painel Executivo de Auditoria.", max_chars=150)

            with col_f3:
                st.markdown("##### 📍 Geolocalização e Data")
                cidade = st.text_input("Cidade da Operação", value="Brasilia")
                estado = st.text_input("Estado (UF)", value="DF", max_chars=2)
                pais = st.text_input("País", value="Brasil")
                latitude_input = st.text_input("Latitude (String)", value="-15.793889")
                longitude_input = st.text_input("Longitude (String)", value="-47.882778")

            st.markdown("<br>", unsafe_allow_html=True)
            botao_enviar = st.form_submit_button("🚀 Enviar e Executar Isolation Forest")

            if botao_enviar:
                if not conta or not cidade or not estado:
                    st.error("❌ Os campos Conta, Cidade e Estado são obrigatórios!")
                else:
                    agora = datetime.now()
                    
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
                        
                        with st.spinner("Aguardando análise de risco do Isolation Forest..."):
                            response = requests.post(url_api, json=payload)
                        
                        if response.status_code in [200, 201]:
                            st.success("✅ Transação processada com sucesso!")
                            st.balloons()
                        else:
                            st.error(f"❌ Falha na Validação (Erro {response.status_code})")
                            st.code(response.text, language="json")
                            
                    except Exception as err:
                        st.error(f"Não foi possível conectar ao servidor backend: {err}")

except Exception as e:
    st.error(f"Erro ao carregar o dashboard: {e}")