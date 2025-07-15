import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Dashboard de Notas Fiscais", layout="wide")

SHEET_ID = "1XpHcU78Jqu-yU3JdoD7M0Cn5Ve4BOtL-6Ew91coBwXE"
GID = "2129036629"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

if "atualizar" not in st.session_state:
    st.session_state.atualizar = 0

if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.session_state.atualizar += 1

# ⚙️ Função principal de carregamento de dados
@st.cache_data
def carregar_dados():
    df = pd.read_csv(CSV_URL)

    # Confere se o cabeçalho veio correto, corrige se necessário
    if "Fornecedor" not in df.columns:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)

    # Define colunas esperadas e renomeia defensivamente
    colunas_esperadas = [
        "Número", "Fornecedor", "Origem", "Status NF", "Emissão", "Valor Total",
        "Observações", "Status Envio", "Data Pagamento", "Prazo Limite"
    ]
    if len(df.columns) >= len(colunas_esperadas):
        df.columns = colunas_esperadas[:len(df.columns)]

    # Converte coluna Emissão para datetime
    df["Emissão"] = pd.to_datetime(df["Emissão"], errors="coerce", dayfirst=True)

    # Remove "R$", pontos e troca vírgula por ponto para Valor Total e converte para float
    df["Valor Total"] = (
        df["Valor Total"]
        .astype(str)
        .str.replace("R\$", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    df["Valor Total"] = pd.to_numeric(df["Valor Total"], errors="coerce").fillna(0)

    # NÃO remover linhas que têm datas em branco, apenas converter datas (NaT onde vazio)
    df["Data Pagamento"] = pd.to_datetime(df["Data Pagamento"], errors="coerce", dayfirst=True)
    df["Prazo Limite"] = pd.to_datetime(df["Prazo Limite"], errors="coerce", dayfirst=True)

    # Opcional: remover linhas que não têm fornecedor ou valor zero, se fizer sentido no seu caso
    df = df.dropna(subset=["Fornecedor"])
    # df = df[df["Valor Total"] > 0]  # Use só se quiser ignorar valores zerados

    # Coluna auxiliar para filtro por mês/ano
    df["AnoMes"] = df["Emissão"].dt.to_period("M").astype(str)

    # Função para status pagamento
    def verificar_status_pagamento(row):
        try:
            if pd.notna(row["Data Pagamento"]) and pd.notna(row["Prazo Limite"]):
                return "Em Dia" if row["Data Pagamento"] <= row["Prazo Limite"] else "Atrasado"
            else:
                return "Sem Dados"
        except Exception:
            return "Erro"

    df["Status Pagamento"] = df.apply(verificar_status_pagamento, axis=1).astype(str)

    return df


df = carregar_dados()

# Adiciona menu lateral
aba = st.sidebar.radio("Escolha a aba:", ["Dashboard NF", "Dados Produtividade", "Dados Requisições"])

if aba == "Dashboard NF":
    # 🧭 A partir daqui segue o dashboard normal...
    st.title("📊 Dashboard - Notas Fiscais Recebidas")

    # Filtros
    fornecedores = df["Fornecedor"].unique()
    fornecedor_selecionado = st.selectbox("Selecionar Fornecedor:", ["Todos"] + sorted(fornecedores.tolist()))
    if fornecedor_selecionado == "Todos":
        df_filtrado = df
    else:
        df_filtrado = df[df["Fornecedor"] == fornecedor_selecionado]

    meses_disponiveis = sorted(df_filtrado["AnoMes"].dropna().unique())
    mes_selecionado = st.selectbox("Selecionar Mês:", ["Todos"] + meses_disponiveis)
    if mes_selecionado == "Todos":
        df_filtrado_mes = df_filtrado
    else:
        df_filtrado_mes = df_filtrado[df_filtrado["AnoMes"] == mes_selecionado]

    # Métricas por mês
    if not df_filtrado_mes.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔢 Total de Notas (mês)", len(df_filtrado_mes))
        with col2:
            st.metric("💰 Valor Total (mês)", f"R$ {df_filtrado_mes['Valor Total'].sum():,.2f}")
    else:
        st.info("Nenhum dado disponível para o mês selecionado.")

    st.divider()

    # Gráfico mensal geral
    valor_por_mes = df.groupby("AnoMes")["Valor Total"].sum().sort_index()
    if not valor_por_mes.empty:
        st.subheader("📆 Total Mensal por Valor")
        st.bar_chart(valor_por_mes)
    else:
        st.info("Sem dados para gerar o gráfico mensal.")

    # Métricas totais
    if not df_filtrado.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🔢 Total de Notas", len(df_filtrado))
        with col2:
            st.metric("💰 Valor Total", f"R$ {df_filtrado['Valor Total'].sum():,.2f}")
    else:
        st.info("Sem dados para calcular totais.")

    st.divider()

    # Gráfico diário
    grafico_total_diario = df_filtrado.groupby("Emissão")["Valor Total"].sum()
    if not grafico_total_diario.empty:
        st.subheader("📅 Evolução Diária dos Valores")
        st.line_chart(grafico_total_diario)
    else:
        st.info("Sem dados para evolução diária.")

    # Top Fornecedores
    top_qtd = df["Fornecedor"].value_counts().head(10)
    top_valor = df.groupby("Fornecedor")["Valor Total"].sum().sort_values(ascending=False).head(10)

    if not top_qtd.empty and not top_valor.empty:
        st.subheader("🏆 Top Fornecedores")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Por Quantidade de Notas**")
            st.bar_chart(top_qtd)
        with col2:
            st.markdown("**Por Valor Total Recebido**")
            st.bar_chart(top_valor)
    else:
        st.info("Sem dados suficientes para exibir os top fornecedores.")

    # Tabela
    if not df_filtrado.empty:
        st.subheader("📋 Tabela de Notas Fiscais")
        st.dataframe(df_filtrado.sort_values("Emissão", ascending=False), use_container_width=True)
    else:
        st.info("Nenhuma nota fiscal para exibir.")

    # Status de envio
    df_filtrado_mes["Status Envio"] = df_filtrado_mes["Status Envio"].fillna("Não Informado").str.strip()
    status_counts = df_filtrado_mes["Status Envio"].value_counts()

    if not status_counts.empty:
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
    else:
        st.info("Sem informações sobre envio ao financeiro.")

    # Status de pagamento
    status_pagamento_counts = df["Status Pagamento"].value_counts()

    if not status_pagamento_counts.empty:
        st.subheader("📈 Indicador de Pagamento (Em dia x Atrasado)")
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
    else:
        st.info("Sem dados sobre pagamento das notas.")
else:
    if aba == "Dados Produtividade":
        st.title("📊 Dados Produtividade")
        st.markdown("---")
        
        # 1. Listar arquivos .xlsx limpos
        pasta = os.getcwd()
        arquivos_xlsx = [arq for arq in os.listdir(pasta) if arq.endswith('_limpa.xlsx') and '2025' in arq]
        
        if not arquivos_xlsx:
            st.warning("Nenhum arquivo .xlsx limpo de 2025 encontrado na pasta.")
        else:
            # 2. Ler e unificar os dados
            lista_df = []
            for arquivo in arquivos_xlsx:
                try:
                    df_mes = pd.read_excel(os.path.join(pasta, arquivo), dtype=str)
                    # Preencher apenas as colunas importantes para baixo (ffill)
                    if 'USUARIO_DE_CRIAÇÃO_RM' in df_mes.columns:
                        df_mes['USUARIO_DE_CRIAÇÃO_RM'] = df_mes['USUARIO_DE_CRIAÇÃO_RM'].fillna(method='ffill')
                    if 'DATA_CRIAÇÃO_RM' in df_mes.columns:
                        df_mes['DATA_CRIAÇÃO_RM'] = df_mes['DATA_CRIAÇÃO_RM'].fillna(method='ffill')
                    # Padroniza o nome das colunas
                    if "USUARIO_DE_CRIAÇÃO_RM" in df_mes.columns and "DATA_CRIAÇÃO_RM" in df_mes.columns:
                        lista_df.append(df_mes[["USUARIO_DE_CRIAÇÃO_RM", "DATA_CRIAÇÃO_RM"]].copy())
                except Exception as e:
                    st.error(f"Erro ao ler {arquivo}: {e}")
            if not lista_df:
                st.warning("Nenhum dado encontrado nas planilhas.")
            else:
                df_prod = pd.concat(lista_df, ignore_index=True)
                df_prod = df_prod.dropna(subset=["USUARIO_DE_CRIAÇÃO_RM", "DATA_CRIAÇÃO_RM"]).copy()
                df_prod["DATA_CRIAÇÃO_RM"] = pd.to_datetime(df_prod["DATA_CRIAÇÃO_RM"], errors="coerce", dayfirst=True)
                df_prod = df_prod.dropna(subset=["DATA_CRIAÇÃO_RM"]).copy()

                # Filtro por mês
                df_prod["AnoMes"] = df_prod["DATA_CRIAÇÃO_RM"].dt.strftime("%Y-%m")
                meses_disponiveis = sorted(df_prod["AnoMes"].unique())
                opcoes_filtro = ["2025 (Todos)"] + meses_disponiveis
                mes_selecionado = st.selectbox("Selecione o mês:", opcoes_filtro)
                if mes_selecionado == "2025 (Todos)":
                    df_filtro = df_prod.copy()
                else:
                    df_filtro = df_prod[df_prod["AnoMes"] == mes_selecionado].copy()

                # 3. Total por requisitante
                total_por_requisitante = df_filtro["USUARIO_DE_CRIAÇÃO_RM"].value_counts().reset_index()
                total_por_requisitante.columns = ["Requisitante", "Total de RMs"]
                st.subheader("Total de RMs por Requisitante")
                st.dataframe(total_por_requisitante, use_container_width=True)
                st.metric("Total Geral de RMs", len(df_filtro))
                # 4. Médias
                st.markdown("---")
                st.subheader("Médias de RMs por Requisitante")
                # Média diária
                diaria = df_filtro.groupby(["USUARIO_DE_CRIAÇÃO_RM", df_filtro["DATA_CRIAÇÃO_RM"].dt.date]).size().groupby("USUARIO_DE_CRIAÇÃO_RM").mean().reset_index()
                diaria.columns = ["Requisitante", "Média Diária"]
                # Média semanal
                semanal = df_filtro.groupby(["USUARIO_DE_CRIAÇÃO_RM", df_filtro["DATA_CRIAÇÃO_RM"].dt.isocalendar().week]).size().groupby("USUARIO_DE_CRIAÇÃO_RM").mean().reset_index()
                semanal.columns = ["Requisitante", "Média Semanal"]
                # Média mensal
                mensal = df_filtro.groupby(["USUARIO_DE_CRIAÇÃO_RM", df_filtro["DATA_CRIAÇÃO_RM"].dt.to_period("M")]).size().groupby("USUARIO_DE_CRIAÇÃO_RM").mean().reset_index()
                mensal.columns = ["Requisitante", "Média Mensal"]
                # Unir todas as médias
                medias = total_por_requisitante.merge(diaria, on="Requisitante", how="left")
                medias = medias.merge(semanal, on="Requisitante", how="left")
                medias = medias.merge(mensal, on="Requisitante", how="left")
                # Formatar médias para uma casa decimal
                for col in ["Média Diária", "Média Semanal", "Média Mensal"]:
                    if col in medias.columns:
                        medias[col] = medias[col].astype(float).round(1)
                st.dataframe(medias, use_container_width=True)

                # Gráficos comparativos interativos ordenados
                st.markdown("---")
                st.subheader("Gráficos Comparativos entre Requisitantes (Interativo)")
                top_n = 20
                # Total de RMs
                plot_total = medias.sort_values("Total de RMs", ascending=False).head(top_n).set_index("Requisitante")
                st.markdown("**Total de RMs por Requisitante**")
                st.bar_chart(plot_total["Total de RMs"])
                # Média Diária
                plot_diaria = medias.sort_values("Média Diária", ascending=False).head(top_n).set_index("Requisitante")
                st.markdown("**Média Diária de RMs por Requisitante**")
                st.bar_chart(plot_diaria["Média Diária"])
                # Média Semanal
                plot_semanal = medias.sort_values("Média Semanal", ascending=False).head(top_n).set_index("Requisitante")
                st.markdown("**Média Semanal de RMs por Requisitante**")
                st.bar_chart(plot_semanal["Média Semanal"])
                # Média Mensal
                plot_mensal = medias.sort_values("Média Mensal", ascending=False).head(top_n).set_index("Requisitante")
                st.markdown("**Média Mensal de RMs por Requisitante**")
                st.bar_chart(plot_mensal["Média Mensal"])
    else:
        st.title(f"📊 {aba}")
        st.info("Em breve...")
