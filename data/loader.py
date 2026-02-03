"""
Carregamento de dados do Google Sheets com cache.
"""
import pandas as pd
from utils.constants import SHEET_ID
from utils.cache import cache_with_ttl
from data.schema import validate_schema


# Rastreador global de valores em Real (descartados)
_valores_em_real_descartados = []


def _detect_currency_and_convert(value):
    """
    Detecta se o valor está em Real ou USD e converte apenas USD.
    Valores em Real (R$) são retornados como None (descartados).
    Valores em USD ($) são convertidos para float.
    
    Returns:
        float se USD, None se Real ou inválido
    """
    global _valores_em_real_descartados
    
    if pd.isna(value) or value == '':
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    value_str = str(value).strip()
    
    # Detecta Real (R$)
    if 'R$' in value_str or 'R $' in value_str:
        _valores_em_real_descartados.append(value_str)
        return None
    
    # Detecta USD ($)
    value_str = value_str.replace('$', '').replace(',', '')
    try:
        return float(value_str)
    except ValueError:
        return None


def get_descartados_valores_em_real():
    """Retorna lista de valores em Real que foram descartados."""
    global _valores_em_real_descartados
    return _valores_em_real_descartados.copy()


def clear_descartados():
    """Limpa o rastreador de valores descartados."""
    global _valores_em_real_descartados
    _valores_em_real_descartados = []


@cache_with_ttl()
def load_data_from_sheets() -> pd.DataFrame:
    """
    Carrega dados da aba KPIs do Google Sheets.
    
    IMPORTANTE: 
    - Valores monetários (Pipeline e Booking TCV) em USD ($) são considerados nos cálculos
    - Valores em Real (R$) são descartados e NÃO são considerados
    - Uma lista de valores em Real descartados pode ser obtida com get_descartados_valores_em_real()
    
    Returns:
        DataFrame com dados da planilha (sem valores em Real).
    
    Raises:
        Exception: se não conseguir conectar à planilha.
    """
    # Limpar rastreador anterior
    clear_descartados()
    
    # Carrega dados via URL pública com o gid correto (aba 1052743275)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1052743275"
    
    df = pd.read_csv(url)
    
    # Normalizar nomes das colunas: remover espaços extras e converter acentos
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace("ã", "a").str.replace("ç", "c").str.replace("é", "e")
    
    # Limpar linhas completamente vazias (com apenas NaN)
    df = df.dropna(how='all')
    
    # Remover espaços das strings em todas as colunas object (texto)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    # Converter colunas monetárias: USD convertido para float, Real descartado (None)
    monetary_cols = ['Pipeline', 'Booking TCV']
    for col in monetary_cols:
        if col in df.columns:
            df[col] = df[col].apply(_detect_currency_and_convert)
    
    # Remover linhas onde BDR está vazio/NaN (dados incompletos)
    df = df.dropna(subset=['BDR'])
    
    validate_schema(df)
    return df
