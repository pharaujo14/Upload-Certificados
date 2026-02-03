"""
Componentes de gráficos de linhas temporais.
"""
import streamlit as st
import plotly.express as px
import pandas as pd


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = None):
    """
    Cria gráfico de linhas.
    
    Args:
        df: DataFrame com dados
        x: coluna para eixo X (temporal)
        y: coluna para eixo Y (valor)
        title: título
        color: coluna para múltiplas linhas
    """
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        markers=True,
        height=400,
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def multi_line_chart(df: pd.DataFrame, x: str, y_cols: list, title: str):
    """
    Cria gráfico com múltiplas linhas (um para cada coluna Y).
    """
    fig = px.line(
        df,
        x=x,
        y=y_cols,
        title=title,
        markers=True,
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
