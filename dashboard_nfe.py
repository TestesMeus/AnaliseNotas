import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")
st.title("📊 Dashboard - Notas Fiscais Recebidas")


SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV_URL)
    st.write("Colunas carregadas:", df.columns.tolist())
    return df

df = carregar_dados()

st.dataframe(df) 

df = df[df["Fornecedor"].notna()]
df["Valor Total"] = pd.to_numeric(df["Valor Total"], errors="coerce")

notas_por_fornecedor = df["Fornecedor"].value_counts()
valor_total_por_fornecedor = df.groupby("Fornecedor")["Valor Total"].sum().sort_values(ascending=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🧾 Quantidade de Notas por Fornecedor")
    st.bar_chart(notas_por_fornecedor)

with col2:
    st.subheader("💰 Valor Total por Fornecedor")
    st.bar_chart(valor_total_por_fornecedor)

st.subheader("📌 Indicadores Gerais")
col3, col4, col5 = st.columns(3)
col3.metric("Total de Fornecedores", df["Fornecedor"].nunique())
col4.metric("Total de Notas", len(df))
col5.metric("Valor Total Geral", f"R$ {df['Valor Total'].sum():,.2f}")
