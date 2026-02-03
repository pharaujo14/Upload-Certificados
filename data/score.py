"""
Calculadora do Score de Performance do BDR.

Fornece a função `compute_bdr_performance_score(df)` que recebe o DataFrame
carregado da aba KPIs e retorna um DataFrame com as colunas:

- `BDR`, `Ano`, `Mes`, `Score de Performance` (valores entre 0 e 1 ou NA quando não elegível)

Regras implementadas:
- Tratamento de divisões por zero retornando 0
- Agrupa por `BDR`, `Ano`, `Mes` (se necessário tenta inferir a partir de colunas de data)
- Normaliza `Booking por Lead` por Min-Max considerando apenas períodos elegíveis (Total Leads >= 30)
- Considera Score apenas quando `Total Leads` >= 30 (casos não elegíveis recebem NA no Score)

Fórmula:
Score = 0.40 * Taxa Geral de Resposta Positiva
      + 0.30 * Taxa de Comparecimento em Reuniões
      + 0.30 * Booking por Lead Normalizado

"""
from __future__ import annotations

import pandas as pd


def compute_bdr_performance_score(df: pd.DataFrame) -> pd.DataFrame:
    """Computa o Score de Performance por BDR agrupado por Ano e Mês.

    Args:
        df: DataFrame com os dados da aba KPIs. Deve conter pelo menos as colunas
            `BDR` e uma combinação de `Ano`/`Mes` ou uma coluna de data que permita
            derivar ano e mês.

    Returns:
        DataFrame com colunas `BDR`, `Ano`, `Mes`, `Score de Performance`.
        O campo `Score de Performance` é um float no intervalo [0, 1] quando o
        grupo é elegível (Total Leads >= 30) ou NA caso contrário.
    """
    df = df.copy()

    # Garantir colunas Ano e Mes (tenta inferir a partir de colunas de data ou
    # aceitar variações com acentos como 'Mês' -> 'M?s' vindo da importação)
    import unicodedata

    def _norm(s: str) -> str:
        return unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode().lower()

    norm_map = {_norm(c): c for c in df.columns}

    if 'ano' in norm_map:
        df['Ano'] = df[norm_map['ano']]
    if 'mes' in norm_map:
        df['Mes'] = df[norm_map['mes']]

    if 'Ano' not in df.columns or 'Mes' not in df.columns:
        # procurar coluna provável de data (ex: 'data' ou 'date')
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'data' in c.lower()]
        if date_cols:
            date_col = date_cols[0]
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df['Ano'] = df[date_col].dt.year
            df['Mes'] = df[date_col].dt.month
        else:
            raise ValueError("Dataframe precisa conter 'Ano' e 'Mes' ou uma coluna de data.")

    # Colunas necessárias (preencher com 0 se ausentes)
    need_cols = [
        'Total positivas', 'Total Negativas',
        'Reuniao Realizada', 'Reuniao Agendada',
        'Booking TCV', 'Total Leads'
    ]
    for c in need_cols:
        if c not in df.columns:
            df[c] = 0

    # Converter para numérico e somar por grupo
    for c in need_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    grouped = (
        df.groupby(['BDR', 'Ano', 'Mes'], as_index=False)
        [need_cols]
        .sum()
    )

    # Taxa Geral de Resposta Positiva
    grouped['taxa_resposta_pos'] = grouped['Total positivas'] / (
        grouped['Total positivas'] + grouped['Total Negativas']
    )
    grouped['taxa_resposta_pos'] = grouped['taxa_resposta_pos'].fillna(0)

    # Taxa de Comparecimento em Reuniões
    grouped['taxa_comparecimento'] = grouped['Reuniao Realizada'] / grouped['Reuniao Agendada']
    grouped.loc[grouped['Reuniao Agendada'] == 0, 'taxa_comparecimento'] = 0
    grouped['taxa_comparecimento'] = grouped['taxa_comparecimento'].fillna(0)

    # Booking por Lead
    grouped['booking_por_lead'] = grouped['Booking TCV'] / grouped['Total Leads']
    grouped.loc[grouped['Total Leads'] == 0, 'booking_por_lead'] = 0

    # Elegibilidade: considerar Score apenas quando Total Leads >= 30
    grouped['eligible'] = grouped['Total Leads'] >= 30

    # Normalizar booking_por_lead por Min-Max considerando apenas períodos elegíveis
    eligible_booking = grouped.loc[grouped['eligible'], 'booking_por_lead']
    if not eligible_booking.empty:
        min_b = eligible_booking.min()
        max_b = eligible_booking.max()
        if pd.isna(min_b) or pd.isna(max_b) or max_b == min_b:
            grouped['booking_norm'] = 0.0
        else:
            grouped['booking_norm'] = ((grouped['booking_por_lead'] - min_b) / (max_b - min_b)).clip(0, 1)
    else:
        grouped['booking_norm'] = 0.0

    # Calcular Score
    grouped['score_raw'] = (
        0.40 * grouped['taxa_resposta_pos']
        + 0.30 * grouped['taxa_comparecimento']
        + 0.30 * grouped['booking_norm']
    )
    # Limitar entre 0 e 1
    grouped['score_clipped'] = grouped['score_raw'].clip(0, 1)

    # Aplicar elegibilidade (Score apenas quando Total Leads >= 30)
    grouped.loc[~grouped['eligible'], 'score_clipped'] = pd.NA

    result = grouped[['BDR', 'Ano', 'Mes', 'score_clipped']].rename(
        columns={'score_clipped': 'Score de Performance'}
    )

    # Ordenar e retornar
    result = result.sort_values(['BDR', 'Ano', 'Mes']).reset_index(drop=True)
    return result
