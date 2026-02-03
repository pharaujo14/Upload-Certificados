"""
Schema da aba KPIs do Google Sheets.
Validacao explicita de estrutura de dados.
"""
from utils.constants import EXPECTED_COLUMNS
import pandas as pd


class SchemaError(Exception):
    """Excecao para erros de schema."""
    pass


def validate_schema(df) -> None:
    """
    Valida se DataFrame contem todas as colunas esperadas.
    
    Raises:
        SchemaError: se esquema estiver incorreto ou vazio.
    """
    if df is None or df.empty:
        raise SchemaError(
            f"Aba vazia ou nao encontrada. "
            "Verifique a planilha Google Sheets."
        )
    
    missing_columns = set(EXPECTED_COLUMNS) - set(df.columns)
    if missing_columns:
        raise SchemaError(
            f"Colunas faltantes no Google Sheets: {missing_columns}\n"
            f"Esperado: {EXPECTED_COLUMNS}"
        )
    
    # Validacao de tipos basicos
    numeric_cols = [
        "Novos Leads", "Leads Reengajamento", "Total Leads",
        "Resposta Positivo LinkedIn", "Resposta Negativa LinkedIn",
        "Resposta Positivo WhatsApp", "Resposta Negativa WhatsApp",
        "Resposta Positivo Ligacao", "Resposta Negativa Ligacao",
        "Resposta Positivo E-mail", "Resposta Negativa E-mail",
        "Total positivas", "Total Negativas",
        "Reuniao Agendada", "Reuniao Aguardando", "Reuniao Realizada",
        "Pipeline", "PoC",
        "Proposta Enviadas", "Propostas Aceitas", "Propostas Recusadas",
        "Booking TCV"
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            try:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception as e:
                raise SchemaError(f"Erro ao converter coluna '{col}' para numerico: {e}")

