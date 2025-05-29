import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de NFe Recebidas", layout="wide")

# Função para carregar e preparar os dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel("nfe-recebidas_01_05_2025-23_05_2025 rev3 (1).xlsx", sheet_name="NFe Recebidas - MÊS 05")
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df.columns = ["Número", "Fornecedor", "Origem", "Status", "Emissão", "Total", "Observações"]
    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)
    df["Total"] = pd.to_numeric(df["Total"], errors="coerce")
    df = df.dropna(subset=["Fornecedor", "Total"])
    return df

df = carregar_dados()

st.title("📊 Dashboard de Análise de Notas Fiscais Recebidas")

# Filtro por fornecedor
fornecedores = df["Fornecedor"].unique()
fornecedor_selecionado = st.selectbox("Selecionar Fornecedor:", ["Todos"] + sorted(fornecedores.tolist()))

df_filtrado = df if fornecedor_selecionado == "Todos" else df[df["Fornecedor"] == fornecedor_selecionado]

col1, col2 = st.columns(2)
with col1:
    st.metric("🔢 Total de Notas", len(df_filtrado))
with col2:
    st.metric("💰 Valor Total", f"R$ {df_filtrado['Total'].sum():,.2f}")

st.divider()

# Gráfico de valor diário
st.subheader("📅 Evolução Diária dos Valores")
grafico_total_diario = df_filtrado.groupby("Emissão")["Total"].sum()
st.line_chart(grafico_total_diario)

# Gráficos por fornecedor
st.subheader("🏆 Top Fornecedores")

top_qtd = df["Fornecedor"].value_counts().head(10)
top_valor = df.groupby("Fornecedor")["Total"].sum().sort_values(ascending=False).head(10)

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
