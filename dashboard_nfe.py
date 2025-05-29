import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
st.title("📊 Dashboard - Notas Fiscais Recebidas")

# URL do Google Sheets exportado como CSV
SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV_URL)

    # Exibe colunas antes do tratamento (debug)
    st.write("🔍 Colunas originais:", df.columns.tolist())
    st.write("🔍 Primeira linha (antes do tratamento):", df.iloc[0].tolist())

    # Ajustar colunas: pegar cabeçalho verdadeiro da linha 1
    df.columns = df.iloc[0]  # redefine cabeçalho
    df = df[1:].reset_index(drop=True)

    # Renomear colunas para uso consistente
    df.columns = ["Número", "Fornecedor", "Origem", "Status", "Emissão", "Valor Total", "Observações"]

    # Converter tipos
    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)
    df["Valor Total"] = (
    df["Valor Total"]
    .astype(str)                # garantir que tudo seja string
    .str.replace(".", "", regex=False)  # remove pontos de milhar (ex: 11.739,00 → 11739,00)
    .str.replace(",", ".", regex=False)  # troca vírgula decimal por ponto
    .str.strip()                # remove espaços
    .astype(float)              # converte para número
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
