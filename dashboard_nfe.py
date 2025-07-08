import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")

# URL do Google Sheets exportado como CSV
SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# Chave para recarregar os dados
if "atualizar" not in st.session_state:
    st.session_state.atualizar = 0

# Botão de atualização manual
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.session_state.atualizar += 1

@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV_URL)
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df.columns = ["Número", "Fornecedor", "Origem", "Status NF", "Emissão", "Valor Total", "Observações", "Status Envio", "Data Pagamento", "Prazo Limite"]

    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)
df["Valor Total"] = (
    df["Valor Total"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
)

df["Valor Total"] = pd.to_numeric(df["Valor Total"], errors="coerce")
df = df.dropna(subset=["Fornecedor", "Valor Total"])

    df = df.dropna(subset=["Fornecedor", "Valor Total"])
    df["AnoMes"] = df["Emissão"].dt.to_period("M").astype(str)

    # ✅ Tratar novas colunas aqui
    df["Data Pagamento"] = pd.to_datetime(df["Data Pagamento"], errors="coerce", dayfirst=True)
    df["Prazo Limite"] = pd.to_datetime(df["Prazo Limite"], errors="coerce", dayfirst=True)
    df["Status Pagamento"] = df.apply(
        lambda row: "Em Dia" if pd.notna(row["Data Pagamento"]) and pd.notna(row["Prazo Limite"]) and row["Data Pagamento"] <= row["Prazo Limite"] else "Atrasado",
        axis=1
    )
    return df

# Carrega os dados
df = carregar_dados()

# --- Visualização ---
st.title("📊 Dashboard - Notas Fiscais Recebidas")

# Filtro por fornecedor
fornecedores = df["Fornecedor"].unique()
fornecedor_selecionado = st.selectbox("Selecionar Fornecedor:", ["Todos"] + sorted(fornecedores.tolist()))
df_filtrado = df if fornecedor_selecionado == "Todos" else df[df["Fornecedor"] == fornecedor_selecionado]

# Filtro por mês (aplicado ao filtrado por fornecedor)
meses_disponiveis = sorted(df_filtrado["AnoMes"].dropna().unique())
mes_selecionado = st.selectbox("Selecionar Mês:", ["Todos"] + meses_disponiveis)
df_filtrado_mes = df_filtrado if mes_selecionado == "Todos" else df_filtrado[df_filtrado["AnoMes"] == mes_selecionado]

# Métricas baseadas no filtro
col1, col2 = st.columns(2)
with col1:
    st.metric("🔢 Total de Notas (mês)", len(df_filtrado_mes))
with col2:
    st.metric("💰 Valor Total (mês)", f"R$ {df_filtrado_mes['Valor Total'].sum():,.2f}")

st.divider()

# Gráfico mensal geral
st.subheader("📆 Total Mensal por Valor")
valor_por_mes = df.groupby("AnoMes")["Valor Total"].sum().sort_index()
st.bar_chart(valor_por_mes)

# Métricas totais
col1, col2 = st.columns(2)
with col1:
    st.metric("🔢 Total de Notas", len(df_filtrado))
with col2:
    st.metric("💰 Valor Total", f"R$ {df_filtrado['Valor Total'].sum():,.2f}")

st.divider()

# Gráfico diário
st.subheader("📅 Evolução Diária dos Valores")
grafico_total_diario = df_filtrado.groupby("Emissão")["Valor Total"].sum()
st.line_chart(grafico_total_diario)

# Top fornecedores
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

# Tabela de dados
st.subheader("📋 Tabela de Notas Fiscais")
st.dataframe(df_filtrado.sort_values("Emissão", ascending=False), use_container_width=True)

# Status de envio (com filtro por mês)
df_filtrado_mes["Status Envio"] = df_filtrado_mes["Status Envio"].fillna("Não Informado").str.strip()
status_counts = df_filtrado_mes["Status Envio"].value_counts()


st.subheader("📤 Situação de Envio ao Financeiro")
col1, col2, col3 = st.columns(3)
col1.metric("Enviadas", status_counts.get("Enviado", 0))
col2.metric("Não Enviadas", status_counts.get("Não Enviado", 0))
col3.metric("Canceladas", status_counts.get("Cancelado", 0))

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

st.subheader("📈 Indicador de Pagamento (Em dia x Atrasado)")

status_pagamento_counts = df["Status Pagamento"].value_counts()

col1, col2 = st.columns(2)
col1.metric("Notas em Dia", status_pagamento_counts.get("Em Dia", 0))
col2.metric("Notas Atrasadas", status_pagamento_counts.get("Atrasado", 0))

fig2, ax2 = plt.subplots(facecolor='none')
ax2.pie(
    status_pagamento_counts,
    labels=status_pagamento_counts.index,
    autopct="%1.1f%%",
    startangle=90,
    textprops={'color': 'white'}
)
ax2.set_facecolor('none')
ax2.axis("equal")
st.pyplot(fig2)

