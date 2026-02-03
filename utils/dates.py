"""
Utilitários para manipulação de datas.
"""
from datetime import datetime, timedelta
import pandas as pd


def get_date_range(start: str, end: str) -> tuple:
    """
    Retorna tupla (data_início, data_fim) em formato datetime.
    """
    return (pd.to_datetime(start), pd.to_datetime(end))


def last_n_weeks(n: int) -> tuple:
    """
    Retorna intervalo dos últimos n dias.
    """
    end = datetime.now()
    start = end - timedelta(days=n*7)
    return (start, end)
