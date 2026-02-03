"""
Componentes de KPI Cards.
"""
import streamlit as st
import pandas as pd


def display_kpi_card(label: str, value: str, delta: str = None, color: str = "blue"):
    """
    Exibe card de KPI com valor e variação opcional.
    
    Args:
        label: nome do KPI
        value: valor principal (string formatada)
        delta: variação (ex: "+5%")
        color: cor do card (blue, green, red)
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label=label, value=value, delta=delta)


def display_kpi_grid(kpis: dict):
    """
    Exibe grid de múltiplos KPIs.
    
    Args:
        kpis: dict com {label: value} ou {label: (value, delta)}
    """
    cols = st.columns(len(kpis))
    
    for col, (label, data) in zip(cols, kpis.items()):
        with col:
            if isinstance(data, tuple):
                value, delta = data
                st.metric(label=label, value=value, delta=delta)
            else:
                st.metric(label=label, value=data)
