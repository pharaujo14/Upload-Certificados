import streamlit as st
import pandas as pd

from dashboards.executive import render_executive_dashboard
from data.loader import load_data_from_sheets
from data.users import get_bdr_users

def pagina_relatorios_bdr_executivo(db):
    st.markdown("## 📊 Relatórios BDR – Visão Executiva")

    # ======================
    # 1. Carregar dados
    # ======================
    df = load_data_from_sheets()

    if df.empty:
        st.warning("Nenhum dado disponível.")
        return

    # ======================
    # 2. Converter data
    # ======================
    df["Semana 1º contato"] = pd.to_datetime(
        df["Semana 1º contato"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    df = df.dropna(subset=["Semana 1º contato"])

    # ======================
    # 3. Filtro por BDR
    # ======================
    bdrs = get_bdr_users(db)
    bdrs = ["Todos"] + bdrs

    selected_bdr = st.selectbox(
        "Filtrar por BDR",
        options=bdrs
    )

    if selected_bdr != "Todos":
        df = df[df["BDR"] == selected_bdr]

    if df.empty:
        st.warning("Nenhum dado para o BDR selecionado.")
        return

    # ======================
    # 4. Filtro por período
    # ======================
    min_date = df["Semana 1º contato"].min()
    max_date = df["Semana 1º contato"].max()

    col1, col2 = st.columns(2)

    with col1:
        data_inicio = st.date_input(
            "Data inicial",
            value=min_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )

    with col2:
        data_fim = st.date_input(
            "Data final",
            value=max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date()
        )

    df = df[
        (df["Semana 1º contato"] >= pd.to_datetime(data_inicio)) &
        (df["Semana 1º contato"] <= pd.to_datetime(data_fim))
    ]

    if df.empty:
        st.warning("Nenhum dado no período selecionado.")
        return

    # ======================
    # 5. Renderizar dashboard
    # ======================
    render_executive_dashboard(df)
