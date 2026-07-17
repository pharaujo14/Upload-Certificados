# pagina_dashboard_leads.py
import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo.collection import Collection
from pymongo.database import Database

# ----------------------------------------------------------------
# Palavras-chave usadas para classificar um cargo como "decisor".
# Ajuste essa lista livremente conforme o critério do negócio.
# A comparação é feita em maiúsculas e por substring (ex: "GERENTE"
# casa com "GERENTE EXECUTIVO DE SEGURANÇA CIBERNÉTICA").
# ----------------------------------------------------------------
DECISOR_KEYWORDS = [
    "DIRETOR", "DIRETORA", "PRESIDENTE", "VICE-PRESIDENTE", "VICE PRESIDENTE",
    "CEO", "CFO", "COO", "CTO", "CIO", "CISO", "CMO",
    "SÓCIO", "SOCIO", "FUNDADOR", "FUNDADORA", "OWNER", "PROPRIETÁRIO", "PROPRIETARIA",
    "GERENTE", "GERÊNCIA", "GERENCIA", "HEAD", "CHEFE",
    "SUPERINTENDENTE", "COORDENADOR", "COORDENADORA", "LÍDER", "LIDER",
]

# ---------- Mongo ----------
def get_collection(db_or_col, db_name: str, col_name: str) -> Collection:
    if isinstance(db_or_col, Collection): client = db_or_col.database.client
    elif isinstance(db_or_col, Database): client = db_or_col.client
    else:                                 client = db_or_col
    return client[db_name][col_name]

# ---------- Utils ----------
def ultimo_valor(v):
    """
    Vários campos da base (contato, celular, telefone, cargo, empresa,
    account_manager, fonte...) são arrays onde novos valores vão sendo
    adicionados ao final com o tempo. Retorna o item mais recente
    (último não vazio) da lista, ou o próprio valor se não for lista.
    """
    if isinstance(v, list):
        vals = [x for x in v if x not in (None, "")]
        return vals[-1] if vals else None
    return v

def safe_str(v):
    if isinstance(v, list):     return ", ".join([str(x) for x in v if x not in (None, "")])
    if isinstance(v, datetime): return v.strftime("%Y-%m-%d %H:%M:%S")
    return "" if v is None else str(v)

def eh_decisor(cargo_str: str) -> bool:
    if not cargo_str:
        return False
    c = cargo_str.upper()
    return any(kw in c for kw in DECISOR_KEYWORDS)

# ---------- Carga de dados (com cache) ----------
@st.cache_data(ttl=300, show_spinner="Carregando dados do dashboard...")
def _carregar_dados(_leads_col, cache_bust: int = 0):
    """
    Busca só os campos necessários (evita trazer o documento inteiro)
    e devolve um DataFrame já com os valores mais recentes resolvidos.
    `cache_bust` existe só para permitir invalidar o cache manualmente.
    """
    projection = {"account_manager": 1, "empresa": 1, "cargo": 1}
    docs = list(_leads_col.find({}, projection))

    rows = []
    for d in docs:
        am_val      = safe_str(ultimo_valor(d.get("account_manager"))) or "(sem account manager)"
        empresa_val = safe_str(ultimo_valor(d.get("empresa"))) or "(sem empresa)"
        cargo_val   = safe_str(ultimo_valor(d.get("cargo")))
        rows.append({
            "account_manager": am_val,
            "empresa": empresa_val,
            "cargo": cargo_val,
            "decisor": eh_decisor(cargo_val),
        })

    return pd.DataFrame(rows, columns=["account_manager", "empresa", "cargo", "decisor"])

# ---------- Página ----------
def pagina_dashboard_leads(db):
    st.markdown("## 📊 Dashboard de Leads")

    leads_col = get_collection(db, "sapinho", "leads")

    if "dashboard_cache_bust" not in st.session_state:
        st.session_state.dashboard_cache_bust = 0

    col_titulo, col_botao = st.columns([5, 1])
    with col_botao:
        if st.button("🔄 Atualizar"):
            st.session_state.dashboard_cache_bust += 1
            st.rerun()

    df = _carregar_dados(leads_col, st.session_state.dashboard_cache_bust)

    total_leads     = len(df)
    total_empresas  = df["empresa"].nunique() if not df.empty else 0
    total_decisores = int(df["decisor"].sum()) if not df.empty else 0
    pct_decisores   = (total_decisores / total_leads * 100) if total_leads else 0

    # ---- Métricas principais ----
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Leads", total_leads)
    m2.metric("Empresas (únicas)", total_empresas)
    m3.metric("Decisores", total_decisores, f"{pct_decisores:.1f}% do total")
    m4.metric("Account Managers ativos", df["account_manager"].nunique() if not df.empty else 0)

    st.caption(
        "Decisor é calculado a partir do cargo mais recente do lead, "
        "buscando termos como diretor, gerente, sócio, CEO, head, entre outros."
    )

    st.markdown("---")

    # ---- Leads por Account Manager ----
    st.markdown("### Leads por Account Manager")
    if df.empty:
        st.info("Nenhum lead na base.")
        return

    am_counts = (
        df["account_manager"]
        .value_counts()
        .reset_index()
        .rename(columns={"count": "Total de Leads", "account_manager": "Account Manager"})
    )

    col_chart, col_table = st.columns([2, 1])
    with col_chart:
        st.bar_chart(am_counts.set_index("Account Manager"))
    with col_table:
        st.dataframe(am_counts, use_container_width=True, hide_index=True)
