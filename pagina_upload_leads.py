import streamlit as st
import pandas as pd
import numpy as np
import re
import unicodedata
from datetime import datetime
from pymongo.collection import Collection
from pymongo.database import Database

# ---------- Utils Mongo ----------
def get_collection(db_or_col, db_name: str, col_name: str) -> Collection:
    if isinstance(db_or_col, Collection):
        client = db_or_col.database.client
    elif isinstance(db_or_col, Database):
        client = db_or_col.client
    else:
        client = db_or_col
    return client[db_name][col_name]

# ---------- Normalização Genérica ----------
def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))

def norm_header(h: str) -> str:
    h = str(h).strip().lower()
    h = _strip_accents(h)
    h = re.sub(r'[^a-z0-9]+', '_', h)          # tudo que não é [a-z0-9] vira "_"
    h = re.sub(r'_+', '_', h).strip('_')       # colapsa múltiplos "_"
    return h

def find_email_col(columns) -> str | None:
    """
    Tenta achar a coluna de e-mail por heurística.
    Ex.: email, e-mail, e_mail, mail, email_address etc.
    """
    normed = {c: norm_header(c) for c in columns}
    # candidatos óbvios
    candidates_exact = {"email", "e_mail", "e_mail_address", "email_address"}
    for original, n in normed.items():
        if n in candidates_exact:
            return original
    # fallback: contém 'mail'
    for original, n in normed.items():
        if 'mail' in n:
            return original
    return None

def val_as_scalar(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s if s else None

def to_list_unique(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [x for x in v if x not in (None, "")]
    return [v] if v not in (None, "") else []

# ---------- Consolidação ----------
def upsert_generic_by_email(col: Collection, email: str, payload: dict, fonte: str):
    """
    - email: chave única
    - payload: dict com colunas -> valor escalar (string) já limpo
    - fonte: string obrigatória desta carga (entra em lista 'fonte')
    Toda coluna vira $addToSet com $each, evitando duplicatas.
    """
    if not email:
        return "skipped_no_email"

    add_to_set = {}
    for k, v in payload.items():
        if k == "email":
            continue
        vals = to_list_unique(v)
        if vals:
            add_to_set[k] = {"$each": vals}

    # fonte sempre como lista e log de upload
    add_to_set.setdefault("fonte", {"$each": []})
    add_to_set["fonte"]["$each"].append(fonte)

    now = datetime.utcnow()
    update = {
        "$setOnInsert": {"email": email, "created_at": now},
        "$set": {"updated_at": now},
        "$push": {"uploads": {"ts": now, "fonte": fonte}}
    }
    if add_to_set:
        update["$addToSet"] = add_to_set

    res = col.update_one({"email": email}, update, upsert=True)
    if res.matched_count == 0 and res.upserted_id:
        return "inserted"
    return "updated"

# ---------- Página Streamlit ----------
def pagina_upload_leads(db):
    st.markdown("## Upload de Leads (CSV/XLSX)")
    st.write("Envie a planilha com uma coluna de **e-mail** (ex.: email, e-mail, e_mail, mail). Todas as demais colunas serão consolidadas no mesmo lead.")

    with st.form("form_upload_leads", clear_on_submit=False):
        fonte = st.text_input("Fonte (obrigatório)", placeholder="Ex.: ABRAS 2025 • Lista palestrantes • Landing X")
        arquivo = st.file_uploader("Arquivo", type=["csv", "xlsx"])
        submit = st.form_submit_button("Processar e Consolidar Leads")

    if not submit:
        return

    # Validação da fonte
    fonte = (fonte or "").strip()
    if not fonte:
        st.warning("Informe a **fonte** antes de processar.")
        return

    if not arquivo:
        st.warning("Selecione um arquivo CSV/XLSX.")
        return

    # Leitura robusta
    try:
        if arquivo.name.lower().endswith(".csv"):
            df = pd.read_csv(arquivo, dtype=str, keep_default_na=False, na_values=[""])
        else:
            df = pd.read_excel(arquivo, dtype=str)
    except Exception as e:
        st.error(f"Falha ao ler o arquivo: {e}")
        return

    if df.empty:
        st.warning("Arquivo sem linhas.")
        return

    # Detecta coluna de e-mail
    email_col = find_email_col(df.columns)
    if not email_col:
        st.error("Não encontrei coluna de e-mail. Renomeie/ajuste sua planilha (ex.: 'email', 'e-mail').")
        return

    # Preview
    st.caption("Prévia (primeiras 50 linhas):")
    st.dataframe(df.head(50))

    leads_col = get_collection(db, "sapinho", "leads")

    inserted = updated = skipped = 0
    cols_norm = {c: norm_header(c) for c in df.columns}  # nomes normalizados para gravar no Mongo

    for _, row in df.iterrows():
        email = val_as_scalar(row[email_col])
        if not email:
            skipped += 1
            continue
        email = email.lower()

        # Monta payload com TODAS as colunas, normalizando nomes e limpando valores
        payload = {}
        for original_col, norm_col in cols_norm.items():
            if norm_col == "email":
                payload["email"] = email
            else:
                payload[norm_col] = val_as_scalar(row[original_col])

        status = upsert_generic_by_email(leads_col, email, payload, fonte)
        if status == "inserted":
            inserted += 1
        elif status == "updated":
            updated += 1
        else:
            skipped += 1

    st.success("Processamento concluído.")
    st.write(f"**Novos:** {inserted} | **Atualizados/Consolidados:** {updated} | **Ignorados (sem e-mail):** {skipped}")
    st.info("Consolidação: todas as colunas viram listas de valores únicos por e-mail. A **fonte** desta carga é anexada ao contato e registrada no histórico (`uploads`).")
