"""
Componentes de funis (conversion funnels).
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def funnel_chart(stages: list, values: list, title: str):
    """
    Cria gráfico de funil.
    
    Args:
        stages: lista de nomes dos estágios
        values: lista de valores para cada estágio
        title: título
    """
    fig = go.Figure(go.Funnel(
        y=stages,
        x=values,
        text=[f"{v:,.0f}" for v in values],
        textposition="inside",
        marker={"color": "rgba(62, 100, 200, 0.8)"},
    ))
    fig.update_layout(
        title=title,
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def conversion_funnel(df: pd.DataFrame, stages: list, title: str):
    """
    Cria funil de conversão com base em DataFrame.
    
    Args:
        df: DataFrame filtrado por acesso
        stages: lista de colunas que representam os estágios
        title: título
    """
    values = [df[stage].sum() for stage in stages if stage in df.columns]
    funnel_chart(stages, values, title)
