import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")

st.title("📊 Dashboard - Análise de Notas Recebidas")

# Upload do arquivo (fora do cache!)
uploaded_file = st.file_uploader("📤 Envie o arquivo da planilha (.xlsx):", type=["xlsx"])

@st.cache_data
def ler_planilha(file):
    return pd.read_excel(file, sheet_name="NFe Recebidas - MÊS 05")

# Se o usuário subiu um arquivo:
if uploaded_file:
    df = ler_planilha(uploaded_file)

    # Limpeza básica de dados
    df = df[df["Fornecedor"].notna()]
    df["Valor Total"] = pd.to_numeric(df["Valor Total"], errors="coerce")
    
    # Agrupamentos
    notas_por_fornecedor = df["Fornecedor"].value_counts()
    valor_total_por_fornecedor = df.groupby("Fornecedor")["Valor Total"].sum().sort_values(ascending=False)

    # Layout em colunas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧾 Quantidade de Notas por Fornecedor")
        st.bar_chart(notas_por_fornecedor)

    with col2:
        st.subheader("💰 Valor Total por Fornecedor")
        st.bar_chart(valor_total_por_fornecedor)

    # Insights adicionais
    st.subheader("📌 Outras Informações Interessantes")
    col3, col4, col5 = st.columns(3)
    col3.metric("Total de Fornecedores", df["Fornecedor"].nunique())
    col4.metric("Total de Notas", len(df))
    col5.metric("Valor Total Geral", f"R$ {df['Valor Total'].sum():,.2f}")

else:
    st.warning("Por favor, envie um arquivo para visualizar o dashboard.")
