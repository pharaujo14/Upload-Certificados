import streamlit as st
from dashboards.operational import render_operational_dashboard
from data.loader import load_data_from_sheets

def pagina_relatorios_bdr_operacional(db):
    st.markdown("## 📈 Relatórios BDR – Visão Operacional")

    user_name = st.session_state.get("nome")

    df = load_data_from_sheets()

    df_bdr = df[df["BDR"] == user_name]

    if df_bdr.empty:
        st.warning("Nenhum dado disponível para seu usuário.")
        return

    render_operational_dashboard(df_bdr)
