"""
Componentes de gráficos de barras.
"""
import streamlit as st
import plotly.express as px
import pandas as pd


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = None):
    """
    Cria gráfico de barras interativo.
    
    Args:
        df: DataFrame com dados
        x: coluna para eixo X
        y: coluna para eixo Y
        title: título do gráfico
        color: coluna para colorir por categoria
    """
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        text_auto=True,
        height=400,
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def horizontal_bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    """
    Cria gráfico de barras horizontais.
    """
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        orientation="h",
        text_auto=True,
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
