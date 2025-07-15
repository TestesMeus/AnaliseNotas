import pandas as pd
import os
import streamlit as st

# Função para carregar dados de Notas Fiscais
@st.cache_data
def carregar_dados_nf(CSV_URL):
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
    if "Valor Total" in df.columns:
        df["Valor Total"] = (
            df["Valor Total"].astype(str)
            .str.replace("R$", "", regex=True)
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

# Função para carregar dados de produtividade
@st.cache_data
def carregar_dados_produtividade(arquivos_xlsx):
    lista_df = []
    for arquivo in arquivos_xlsx:
        try:
            df_mes = pd.read_excel(os.path.join(os.getcwd(), arquivo), dtype=str)
            if 'USUARIO_DE_CRIAÇÃO_RM' in df_mes.columns:
                df_mes['USUARIO_DE_CRIAÇÃO_RM'] = df_mes['USUARIO_DE_CRIAÇÃO_RM'].fillna(method='ffill')
            if 'DATA_CRIAÇÃO_RM' in df_mes.columns:
                df_mes['DATA_CRIAÇÃO_RM'] = df_mes['DATA_CRIAÇÃO_RM'].fillna(method='ffill')
            if "USUARIO_DE_CRIAÇÃO_RM" in df_mes.columns and "DATA_CRIAÇÃO_RM" in df_mes.columns:
                lista_df.append(df_mes[["USUARIO_DE_CRIAÇÃO_RM", "DATA_CRIAÇÃO_RM"]].copy())
        except Exception as e:
            st.error(f"Erro ao ler {arquivo}: {e}")
    if not lista_df:
        return pd.DataFrame()
    df_prod = pd.concat(lista_df, ignore_index=True)
    df_prod = df_prod.dropna(subset=["USUARIO_DE_CRIAÇÃO_RM", "DATA_CRIAÇÃO_RM"]).copy()
    df_prod["DATA_CRIAÇÃO_RM"] = pd.to_datetime(df_prod["DATA_CRIAÇÃO_RM"], errors="coerce", dayfirst=True)
    df_prod = df_prod.dropna(subset=["DATA_CRIAÇÃO_RM"]).copy()
    df_prod["AnoMes"] = df_prod["DATA_CRIAÇÃO_RM"].dt.strftime("%Y-%m")
    return df_prod

# Função para carregar dados de requisições
@st.cache_data
def carregar_dados_requisicoes(arquivos_xlsx):
    lista_df = []
    for arquivo in arquivos_xlsx:
        try:
            df_mes = pd.read_excel(os.path.join(os.getcwd(), arquivo), dtype=str)
            for col in ['DATA_AUTORIZACAO_RM', 'DATA_CRIAÇÃO_SC', 'CENTRO_CUSTO_OC']:
                if col in df_mes.columns:
                    df_mes[col] = df_mes[col].ffill()
            if "DATA_AUTORIZACAO_RM" in df_mes.columns and "DATA_CRIAÇÃO_SC" in df_mes.columns and "CENTRO_CUSTO_OC" in df_mes.columns:
                lista_df.append(df_mes[["DATA_AUTORIZACAO_RM", "DATA_CRIAÇÃO_SC", "CENTRO_CUSTO_OC"]].copy())
        except Exception as e:
            st.error(f"Erro ao ler {arquivo}: {e}")
    if not lista_df:
        return pd.DataFrame()
    df_req = pd.concat(lista_df, ignore_index=True)
    df_req["DATA_AUTORIZACAO_RM"] = pd.to_datetime(df_req["DATA_AUTORIZACAO_RM"], errors="coerce", dayfirst=True)
    df_req["DATA_CRIAÇÃO_SC"] = pd.to_datetime(df_req["DATA_CRIAÇÃO_SC"], errors="coerce", dayfirst=True)
    df_req["Dias_RM_para_SC"] = (df_req["DATA_CRIAÇÃO_SC"].dt.normalize() - df_req["DATA_AUTORIZACAO_RM"].dt.normalize()).dt.days
    df_req["AnoMes"] = df_req["DATA_AUTORIZACAO_RM"].dt.strftime("%Y-%m")
    return df_req 