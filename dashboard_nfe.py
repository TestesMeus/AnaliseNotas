import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
st.title("📊 Dashboard - Notas Fiscais Recebidas")

# URL do Google Sheets exportado como CSV
SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV_URL)

    # Ajustar colunas: pegar cabeçalho verdadeiro da linha 1
    df.columns = df.iloc[0]  # redefine o cabeçalho
    df = df[1:].reset_index(drop=True)

    # Garantir nomes consistentes
    df.columns = ["Número", "Fornecedor", "Origem", "Status NF", "Emissão", "Valor Total", "Observações", "Status Envio"]

    # Converter tipos
    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)
    df["Valor Total"] = (
        df["Valor Total"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .astype(float)
    )

    # Limpar dados
    df = df.dropna(subset=["Fornecedor", "Valor Total"])

    return df
# Carregar dados
df = carregar_dados()

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


df["Status Envio"] = df["Status Envio"].fillna("Não Informado").str.strip()

status_counts = df["Status Envio"].value_counts()



st.subheader("📤 Situação de Envio ao Financeiro")

col1, col2, col3 = st.columns(3)
col1.metric("Enviadas", status_counts.get("Enviado", 0))
col2.metric("Não Enviadas", status_counts.get("Não Enviado", 0))
col3.metric("Canceladas", status_counts.get("Cancelado", 0))

# Criar gráfico com fundo transparente e textos brancos
fig, ax = plt.subplots(facecolor='none')  # Fundo da figura transparente
ax.pie(
    status_counts,
    labels=status_counts.index,
    autopct="%1.1f%%",
    startangle=90,
    textprops={'color': 'white'}  # Textos brancos
)
ax.set_facecolor('none')  # Fundo do gráfico (ax) transparente
ax.axis("equal")
st.pyplot(fig)




# Define o tempo de atualização (em segundos)
refresh_interval = 60  # 60 segundos = 1 minuto

# Verifica se a sessão começou
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# Verifica se já passou o tempo de atualização
elapsed_time = time.time() - st.session_state.start_time
if elapsed_time > refresh_interval:
    st.session_state.start_time = time.time()  # Reinicia o tempo
    st.experimental_rerun()
else:
    # Mostra tempo restante para atualizar
    st.info(f"🔄 Atualizando em {int(refresh_interval - elapsed_time)} segundos...")