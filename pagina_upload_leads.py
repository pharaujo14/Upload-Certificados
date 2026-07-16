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

# ---------- Resumo final (sem depender de st.dialog) ----------
def mostrar_resultado(inserted: int, updated: int, skipped: int, erros: list):
    st.toast("Processamento concluído!", icon="✅")

    with st.container(border=True):
        st.markdown("### 📋 Resultado do processamento")
        c1, c2, c3 = st.columns(3)
        c1.metric("Novos", inserted)
        c2.metric("Atualizados", updated)
        c3.metric("Ignorados", skipped)

        if erros:
            st.error(f"⚠️ {len(erros)} erro(s) encontrado(s) durante o processamento:")
            for e in erros[:20]:
                st.write(f"- Linha {e['linha']} (email: `{e.get('email') or '-'}`): {e['erro']}")
            if len(erros) > 20:
                st.caption(f"... e mais {len(erros) - 20} erro(s) não exibido(s).")
        else:
            st.success("✅ Nenhum erro durante o processamento.")

        if st.button("OK, entendi", type="primary"):
            st.session_state.pop("resultado_upload", None)
            st.rerun()

# ---------- Página Streamlit ----------
def pagina_upload_leads(db):
    st.markdown("## Upload de Leads (CSV/XLSX)")
    st.write("Envie a planilha com uma coluna de **e-mail** (ex.: email, e-mail, e_mail, mail). Todas as demais colunas serão consolidadas no mesmo lead.")

    # Se há um resultado pendente de uma execução anterior, mostra antes de tudo
    if "resultado_upload" in st.session_state:
        r = st.session_state["resultado_upload"]
        mostrar_resultado(r["inserted"], r["updated"], r["skipped"], r["erros"])
        st.divider()

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

    total = len(df)
    inserted = updated = skipped = 0
    erros = []
    cols_norm = {c: norm_header(c) for c in df.columns}  # nomes normalizados para gravar no Mongo

    progress_bar = st.progress(0, text=f"Iniciando processamento... 0/{total} (0%)")

    for i, (_, row) in enumerate(df.iterrows(), start=1):
        email = val_as_scalar(row[email_col])
        try:
            if not email:
                skipped += 1
            else:
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
        except Exception as e:
            skipped += 1
            erros.append({"linha": i, "email": email, "erro": str(e)})

        pct = i / total
        progress_bar.progress(pct, text=f"Processando... {i}/{total} ({pct * 100:.0f}%)")

    progress_bar.progress(1.0, text=f"Processamento concluído! {total}/{total} (100%)")

    # Guarda o resultado e recarrega a página para mostrar o resumo destacado no topo
    st.session_state["resultado_upload"] = {
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "erros": erros,
    }
    st.rerun()