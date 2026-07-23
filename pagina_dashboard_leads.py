# pagina_dashboard_leads.py
import streamlit as st
import pandas as pd
from datetime import datetime
from pymongo.collection import Collection
from pymongo.database import Database

# ----------------------------------------------------------------
# Rótulo usado quando o cargo do lead está vazio, e quando o cargo
# existe mas não foi encontrado na tabela "cargos" (ex: ainda não
# passou pelo De-Para de unificação, ou é um valor novo na base).
# ----------------------------------------------------------------
SEM_CARGO_LABEL = "(sem cargo)"
NAO_CLASSIFICADO_LABEL = "(não classificado)"

# Classificação considerada "decisor" para efeito da métrica principal.
# Ajuste aqui se o rótulo na tabela "cargos" for diferente.
CLASSIFICACAO_DECISOR = "Decisor"


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

# ---------- Carga de dados (com cache) ----------
@st.cache_data(ttl=300, show_spinner="Carregando dados do dashboard...")
def _carregar_mapa_classificacao(_cargos_col, cache_bust: int = 0) -> dict:
    """
    Busca a tabela de cargos (nome -> classificação) já cadastrada no banco
    e devolve um dicionário para lookup em memória. A tabela é pequena
    (algumas centenas de cargos), então isso é bem mais barato do que fazer
    um $lookup por lead.
    """
    docs = _cargos_col.find({}, {"nome": 1, "classificacao": 1})
    return {
        d["nome"]: d.get("classificacao") or NAO_CLASSIFICADO_LABEL
        for d in docs
        if d.get("nome")
    }

@st.cache_data(ttl=300, show_spinner="Carregando dados do dashboard...")
def _carregar_dados(_leads_col, _cargos_col, cache_bust: int = 0):
    """
    Busca só os campos necessários (evita trazer o documento inteiro),
    resolve o valor mais recente de cargo/account_manager/empresa, e
    cruza o cargo com a tabela "cargos" para obter a classificação.
    `cache_bust` existe só para permitir invalidar o cache manualmente.
    """
    mapa_classificacao = _carregar_mapa_classificacao(_cargos_col, cache_bust)

    projection = {"account_manager": 1, "empresa": 1, "cargo": 1}
    docs = list(_leads_col.find({}, projection))

    rows = []
    for d in docs:
        am_val      = safe_str(ultimo_valor(d.get("account_manager"))) or "(sem account manager)"
        empresa_val = safe_str(ultimo_valor(d.get("empresa"))) or "(sem empresa)"
        cargo_val   = safe_str(ultimo_valor(d.get("cargo")))

        if not cargo_val:
            classificacao_val = SEM_CARGO_LABEL
        else:
            classificacao_val = mapa_classificacao.get(cargo_val, NAO_CLASSIFICADO_LABEL)

        rows.append({
            "account_manager": am_val,
            "empresa": empresa_val,
            "cargo": cargo_val,
            "classificacao": classificacao_val,
        })

    return pd.DataFrame(rows, columns=["account_manager", "empresa", "cargo", "classificacao"])

# ---------- Página ----------
def pagina_dashboard_leads(db):
    st.markdown("## 📊 Dashboard de Leads")

    leads_col  = get_collection(db, "sapinho", "leads")
    cargos_col = get_collection(db, "sapinho", "cargos")

    if "dashboard_cache_bust" not in st.session_state:
        st.session_state.dashboard_cache_bust = 0

    col_titulo, col_botao = st.columns([5, 1])
    with col_botao:
        if st.button("🔄 Atualizar"):
            st.session_state.dashboard_cache_bust += 1
            st.rerun()

    df = _carregar_dados(leads_col, cargos_col, st.session_state.dashboard_cache_bust)

    total_leads     = len(df)
    total_empresas  = df["empresa"].nunique() if not df.empty else 0
    total_decisores = int((df["classificacao"] == CLASSIFICACAO_DECISOR).sum()) if not df.empty else 0
    pct_decisores   = (total_decisores / total_leads * 100) if total_leads else 0

    # ---- Métricas principais ----
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Leads", total_leads)
    m2.metric("Empresas (únicas)", total_empresas)
    m3.metric("Decisores", total_decisores, f"{pct_decisores:.1f}% do total")
    m4.metric("Account Managers ativos", df["account_manager"].nunique() if not df.empty else 0)

    st.caption(
        "Decisor é calculado a partir da classificação cadastrada para o cargo "
        "mais recente do lead, na tabela de cargos do banco."
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

    st.markdown("---")

    # ---- Leads por Classificação ----
    st.markdown("### Leads por Classificação")

    classificacao_counts = (
        df["classificacao"]
        .value_counts()
        .reset_index()
        .rename(columns={"count": "Total de Leads", "classificacao": "Classificação"})
    )

    col_chart2, col_table2 = st.columns([2, 1])
    with col_chart2:
        st.bar_chart(classificacao_counts.set_index("Classificação"))
    with col_table2:
        st.dataframe(classificacao_counts, use_container_width=True, hide_index=True)

    # Cargos que caíram em "(não classificado)" merecem atenção: ou é um
    # cargo novo ainda sem De-Para, ou faltou incluir na planilha de
    # classificação. Mostra a lista para facilitar a manutenção da tabela.
    nao_classificados = sorted(
        df.loc[df["classificacao"] == NAO_CLASSIFICADO_LABEL, "cargo"].unique()
    )
    if nao_classificados:
        with st.expander(f"⚠️ {len(nao_classificados)} cargo(s) sem classificação cadastrada"):
            st.dataframe(pd.DataFrame({"Cargo": nao_classificados}), use_container_width=True, hide_index=True)