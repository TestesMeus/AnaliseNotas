import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")

# URL do Google Sheets exportado como CSV
SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# Estado da sessão para armazenar quantidade anterior de linhas
if "linhas_anteriores" not in st.session_state:
    st.session_state.linhas_anteriores = 0
if "parar_refresh" not in st.session_state:
    st.session_state.parar_refresh = False

# Só faz refresh se ainda não pediu para parar
if not st.session_state.parar_refresh:
    count = st_autorefresh(interval=5_000, limit=None, key="autorefresh")

@st.cache_data
def carregar_dados(_chave):
    df = pd.read_csv(CSV_URL)

    # Ajustar colunas: pegar cabeçalho verdadeiro da linha 1
    df.columns = df.iloc[0]  # redefine o cabeçalho
    df = df[1:].reset_index(drop=True)

    df.columns = ["Número", "Fornecedor", "Origem", "Status NF", "Emissão", "Valor Total", "Observações", "Status Envio"]

    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)
    df["Valor Total"] = (
        df["Valor Total"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .astype(float)
    )

    df = df.dropna(subset=["Fornecedor", "Valor Total"])

    return df

# Usar contador se existir, senão 0
chave_refresh = count if 'count' in locals() else 0
df = carregar_dados(chave_refresh)

# Verifica se houve mudança
qtd_atual = len(df)
if qtd_atual == st.session_state.linhas_anteriores:
    st.session_state.parar_refresh = True
else:
    st.session_state.linhas_anteriores = qtd_atual

# --- Visualização ---
st.title("📊 Dashboard - Notas Fiscais Recebidas")

# Filtro por fornecedor
fornecedores = df["Fornecedor"].unique()
fornecedor_selecionado = st.selectbox("Selecionar Fornecedor:", ["Todos"] + sorted(fornecedores.tolist()))
df_filtrado = df if fornecedor_selecionado == "Todos" else df[df["Fornecedor"] == fornecedor_selecionado]

# Métricas
col1, col2 = st.columns(2)
with col1:
    st.metric("🔢 Total de Notas", len(df_filtrado))
with col2:
    st.metric("💰 Valor Total", f"R$ {df_filtrado['Valor Total'].sum():,.2f}")

st.divider()

# Gráfico por data
st.subheader("📅 Evolução Diária dos Valores")
grafico_total_diario = df_filtrado.groupby("Emissão")["Valor Total"].sum()
st.line_chart(grafico_total_diario)

# Gráficos por fornecedor
st.subheader("🏆 Top Fornecedores")
top_qtd = df["Fornecedor"].value_counts().head(10)
top_valor = df.groupby("Fornecedor")["Valor Total"].sum().sort_values(ascending=False).head(10)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Por Quantidade de Notas**")
    st.bar_chart(top_qtd)
with col2:
    st.markdown("**Por Valor Total Recebido**")
    st.bar_chart(top_valor)

# Tabela
st.subheader("📋 Tabela de Notas Fiscais")
st.dataframe(df_filtrado.sort_values("Emissão", ascending=False), use_container_width=True)

# Situação de envio
df["Status Envio"] = df["Status Envio"].fillna("Não Informado").str.strip()
status_counts = df["Status Envio"].value_counts()

st.subheader("📤 Situação de Envio ao Financeiro")

col1, col2, col3 = st.columns(3)
col1.metric("Enviadas", status_counts.get("Enviado", 0))
col2.metric("Não Enviadas", status_counts.get("Não Enviado", 0))
col3.metric("Canceladas", status_counts.get("Cancelado", 0))

# Gráfico pizza
fig, ax = plt.subplots(facecolor='none')
ax.pie(
    status_counts,
    labels=status_counts.index,
    autopct="%1.1f%%",
    startangle=90,
    textprops={'color': 'white'}
)
ax.set_facecolor('none')
ax.axis("equal")
st.pyplot(fig)
