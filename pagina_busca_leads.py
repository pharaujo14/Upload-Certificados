# pagina_busca_e_edicao_leads_campos.py
import os
import streamlit as st
from datetime import datetime, timezone
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo import ReturnDocument
from bson.regex import Regex
from bson import ObjectId

PROTECTED_FIELDS = {"_id", "email", "created_at", "updated_at", "fonte"}

# ---------- Mongo ----------
def get_collection(db_or_col, db_name: str, col_name: str) -> Collection:
    if isinstance(db_or_col, Collection): client = db_or_col.database.client
    elif isinstance(db_or_col, Database): client = db_or_col.client
    else:                                 client = db_or_col
    return client[db_name][col_name]

def _rx(q: str) -> Regex:
    return Regex((q or "").strip(), "i")

# ---------- Utils ----------
def safe_str(v):
    if isinstance(v, list):     return ", ".join([str(x) for x in v if x not in (None, "")])
    if isinstance(v, datetime): return v.strftime("%Y-%m-%d %H:%M:%S")
    return "" if v is None else str(v)

def to_list_from_textarea(txt: str):
    if not txt: return []
    vals = [ln.strip() for ln in txt.splitlines()]
    return [v for v in vals if v]

def ultimo_valor(v):
    """
    Vários campos da base (contato, celular, telefone, cargo, empresa, fonte...)
    são arrays onde novos valores vão sendo adicionados ao final com o tempo.
    Retorna o item mais recente (último não vazio) da lista, ou o próprio
    valor se não for uma lista.
    """
    if isinstance(v, list):
        vals = [x for x in v if x not in (None, "")]
        return vals[-1] if vals else None
    return v

def _current_user():
    return (st.session_state.get("user_name")
            or st.session_state.get("email")
            or os.getenv("USER")
            or "desconhecido")

# ---------- Diff & Update ----------
def diff_docs(original: dict, edited: dict):
    to_set, to_unset, changes = {}, {}, []
    # removidos
    for k in original.keys() - edited.keys():
        if k in PROTECTED_FIELDS: continue
        to_unset[k] = ""
        changes.append({"field": k, "before": original.get(k), "after": None})
    # adicionados/alterados
    for k in edited.keys():
        if k in PROTECTED_FIELDS: continue
        before, after = original.get(k), edited.get(k)
        if before != after:
            to_set[k] = after
            changes.append({"field": k, "before": before, "after": after})
    return changes, to_set, to_unset

def _build_id_filter(doc_id):
    """
    Casa _id se for ObjectId OU string.
    Se doc_id já for ObjectId -> usa direto.
    Se for string com formato de ObjectId -> tenta os dois: ObjectId e string.
    Caso contrário -> usa como string mesmo.
    """
    if isinstance(doc_id, ObjectId):
        return {"_id": doc_id}
    if isinstance(doc_id, str):
        try:
            oid = ObjectId(doc_id)
            return {"$or": [{"_id": oid}, {"_id": doc_id}]}
        except Exception:
            return {"_id": doc_id}
    # tipo inesperado:
    return {"_id": doc_id}

def update_lead_by_id_or_email(leads_col: Collection, doc, to_set: dict, to_unset: dict):
    """
    1) Tenta por _id (robusto a str/ObjectId)
    2) Se não casar, tenta por email escalar (se existir)
    Sempre grava updated_at e __touch.
    Retorna dict com matched/modified/method usado.
    """
    now = datetime.now(timezone.utc)
    to_set = dict(to_set or {})
    to_unset = dict(to_unset or {})
    to_set["updated_at"] = now
    to_set["__touch"] = now.isoformat()

    ops = {}
    if to_set:   ops["$set"] = to_set
    if to_unset: ops["$unset"] = to_unset
    if not ops:
        return {"matched": 0, "modified": 0, "method": None}

    # 1) por _id
    id_filter = _build_id_filter(doc.get("_id"))
    before = leads_col.find_one(id_filter, projection={"_id": 1})
    if before:
        after = leads_col.find_one_and_update(id_filter, ops, return_document=ReturnDocument.AFTER)
        return {"matched": 1 if after else 0, "modified": 1 if after else 0, "method": "by_id", "after": after}

    # 2) fallback por email (se existir)
    email_val = doc.get("email")
    if isinstance(email_val, list):
        email_val = email_val[0] if email_val else None
    if isinstance(email_val, str):
        email_val = email_val.strip().lower()
    if email_val:
        after = leads_col.find_one_and_update({"email": email_val}, ops, return_document=ReturnDocument.AFTER)
        return {"matched": 1 if after else 0, "modified": 1 if after else 0, "method": "by_email", "after": after}

    return {"matched": 0, "modified": 0, "method": "none"}

def delete_lead_by_id_or_email(leads_col: Collection, doc):
    """
    Exclui o lead por _id (robusto a str/ObjectId) e, se não casar,
    tenta por email escalar. Retorna dict com deleted_count/method.
    """
    id_filter = _build_id_filter(doc.get("_id"))
    res = leads_col.delete_one(id_filter)
    if res.deleted_count:
        return {"deleted": res.deleted_count, "method": "by_id"}

    email_val = doc.get("email")
    if isinstance(email_val, list):
        email_val = email_val[0] if email_val else None
    if isinstance(email_val, str):
        email_val = email_val.strip().lower()
    if email_val:
        res = leads_col.delete_one({"email": email_val})
        return {"deleted": res.deleted_count, "method": "by_email"}

    return {"deleted": 0, "method": "none"}

# ---------- Página ----------
def pagina_busca_leads(db):
    st.markdown("## Busca e Edição de Leads")
    st.write("Pesquise por **nome**, **empresa** ou **email**. Edite nos cartões (exceto `email` e `fonte`).")

    leads_col = get_collection(db, "sapinho", "leads")
    logs_col  = get_collection(db, "sapinho", "logs")

    # Busca
    with st.form("form_busca_leads", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1: q_nome    = st.text_input("Nome")
        with c2: q_empresa = st.text_input("Empresa")
        with c3: q_email   = st.text_input("Email")
        c4, c5 = st.columns(2)
        with c4: page_size   = st.selectbox("Itens por página", [10, 20, 50, 100], index=1)
        with c5: ordenar_por = st.selectbox("Ordenar por", ["Mais recentes (updated_at)", "Mais antigos (updated_at)"])
        submitted = st.form_submit_button("Buscar")

    # ----------------------------------------------------------------
    # Os critérios de busca ficam guardados em session_state e só são
    # atualizados quando o form de busca é de fato submetido. Assim,
    # cliques em paginação/salvar/excluir (que reexecutam o app inteiro)
    # não perdem a busca corrente.
    # ----------------------------------------------------------------
    if "lead_page" not in st.session_state:
        st.session_state.lead_page = 1
    if "search_criteria" not in st.session_state:
        st.session_state.search_criteria = None

    if submitted:
        st.session_state.search_criteria = {
            "q_nome": q_nome,
            "q_empresa": q_empresa,
            "q_email": q_email,
            "page_size": page_size,
            "ordenar_por": ordenar_por,
        }
        st.session_state.lead_page = 1

    criteria = st.session_state.search_criteria
    if criteria is None:
        # Nunca buscou nesta sessão ainda.
        return

    ors = []
    if criteria["q_nome"]:    ors.append({"contato": _rx(criteria["q_nome"])})
    if criteria["q_empresa"]: ors.append({"empresa": _rx(criteria["q_empresa"])})
    if criteria["q_email"]:   ors.append({"email": _rx(criteria["q_email"])})
    query = {"$or": ors} if ors else {}

    page_size = criteria["page_size"]
    sort_field = "updated_at"
    sort_dir   = -1 if "Mais recentes" in criteria["ordenar_por"] else 1

    current_page = st.session_state.lead_page
    skip = (current_page - 1) * page_size

    total = leads_col.count_documents(query)
    docs = list(leads_col.find(query).sort(sort_field, sort_dir).skip(skip).limit(page_size))
    last_page = max(1, (total + page_size - 1) // page_size)
    st.caption(f"Encontrados: {total} • Página {current_page} de {last_page}")

    if not docs:
        st.info("Nenhum lead encontrado.")
        return

    # Resultado da última operação por doc
    st.session_state.setdefault("last_update", {})

    # Cards
    for d in docs:
        doc_id = d.get("_id")
        skey = str(doc_id)
        confirm_key = f"confirm_delete_{skey}"

        # ---- Cabeçalho do card: Nome / Email / Cargo / Telefone ----
        # "nome" vem do campo "contato" (array) -> pega o mais recente.
        # "telefone" prioriza o campo "celular" (mais recente); se não
        # existir, cai para o campo "telefone" (também mais recente).
        nome_disp     = safe_str(ultimo_valor(d.get("contato"))) or "(sem nome)"
        email_disp    = safe_str(d.get("email")) or "(sem email)"
        cargo_disp    = safe_str(ultimo_valor(d.get("cargo"))) or "(sem cargo)"
        telefone_val  = ultimo_valor(d.get("celular")) or ultimo_valor(d.get("telefone"))
        telefone_disp = safe_str(telefone_val) or "(sem telefone)"
        header = f"{nome_disp}  —  {email_disp}  —  {cargo_disp}  —  {telefone_disp}"

        with st.expander(header):
            # Read-only
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Email (fixo)", value=safe_str(d.get("email")), disabled=True, key=f"ro_email_{skey}")
                st.text_input("Criado em", value=safe_str(d.get("created_at")), disabled=True, key=f"ro_created_{skey}")
            with col2:
                st.text_input("Fonte (fixo)", value=safe_str(d.get("fonte")), disabled=True, key=f"ro_fonte_{skey}")
                st.text_input("Atualizado em", value=safe_str(d.get("updated_at")), disabled=True, key=f"ro_updated_{skey}")

            st.markdown("---")

            # Form de edição
            with st.form(f"edit_{skey}", clear_on_submit=False):
                edited = {k: d.get(k) for k in d.keys()}
                normal_keys = [k for k in d.keys() if k not in PROTECTED_FIELDS and k != "_id"]

                for k in sorted(normal_keys):
                    v = d.get(k)
                    if isinstance(v, list):
                        default_txt = "\n".join([str(x) for x in v if x not in (None, "")])
                        txt = st.text_area(k, value=default_txt, placeholder="Um valor por linha", height=100, key=f"ta_{k}_{skey}")
                        edited[k] = to_list_from_textarea(txt)
                    elif isinstance(v, datetime):
                        st.text_input(f"{k} (data/hora)", value=safe_str(v), disabled=True, key=f"ro_dt_{k}_{skey}")
                        edited[k] = v
                    elif isinstance(v, dict):
                        default_txt = "\n".join(f"{kk}: {vv}" for kk, vv in v.items())
                        txt = st.text_area(f"{k} (objeto: chave:valor por linha)", value=default_txt, height=100, key=f"ta_obj_{k}_{skey}")
                        new_dict = {}
                        for ln in txt.splitlines():
                            if ":" in ln:
                                kk, vv = ln.split(":", 1)
                                new_dict[kk.strip()] = vv.strip()
                        edited[k] = new_dict
                    else:
                        edited[k] = st.text_input(k, value=safe_str(v), key=f"in_{k}_{skey}")

                c1, c2, c3 = st.columns(3)
                with c1: salvar   = st.form_submit_button("Salvar alterações")
                with c2: cancelar = st.form_submit_button("Cancelar (recarregar)")
                with c3: excluir  = st.form_submit_button("🗑️ Excluir da base")

            if cancelar:
                st.rerun()

            if salvar:
                try:
                    # protege campos
                    for pf in PROTECTED_FIELDS:
                        if pf in d:
                            edited[pf] = d[pf]

                    changes, to_set, to_unset = diff_docs(d, edited)
                    res = update_lead_by_id_or_email(leads_col, d, to_set, to_unset)
                    st.session_state["last_update"][skey] = {"save": {"res": {"matched": res["matched"], "modified": res["modified"], "method": res.get("method")}, "changes": changes}}
                    if res["matched"] == 0:
                        st.warning("Nada salvo: filtro não encontrou o documento (verificar _id/email).")
                    else:
                        logs_col.insert_one({
                            "type": "lead_update",
                            "doc_id": d.get("_id"),
                            "email": d.get("email"),
                            "changed_by": _current_user(),
                            "changes": changes,
                            "ts": datetime.now(timezone.utc),
                            "update_result": {"matched": res["matched"], "modified": res["modified"], "method": res.get("method")}
                        })
                        if changes:
                            st.success("Alterações salvas.")
                        else:
                            st.info("Nenhum campo alterado.")
                except Exception as e:
                    st.session_state["last_update"][skey] = {"error": str(e)}
                    st.error(str(e))

            if excluir:
                # Excluir é destrutivo: só marca a intenção e pede confirmação
                # explícita antes de apagar de fato.
                st.session_state[confirm_key] = True

            # ---- Confirmação de exclusão (fora do form) ----
            if st.session_state.get(confirm_key):
                st.warning(f"Tem certeza que deseja excluir **{nome_disp}** ({email_disp}) da base? Essa ação não pode ser desfeita.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Sim, excluir definitivamente", key=f"confirm_yes_{skey}"):
                        try:
                            res = delete_lead_by_id_or_email(leads_col, d)
                            if res["deleted"]:
                                logs_col.insert_one({
                                    "type": "lead_delete",
                                    "doc_id": d.get("_id"),
                                    "email": d.get("email"),
                                    "changed_by": _current_user(),
                                    "ts": datetime.now(timezone.utc),
                                    "delete_result": res
                                })
                                st.session_state.pop(confirm_key, None)
                                st.success("Lead excluído.")
                                st.rerun()
                            else:
                                st.error("Não foi possível excluir: documento não encontrado (verificar _id/email).")
                        except Exception as e:
                            st.error(str(e))
                with cc2:
                    if st.button("Cancelar exclusão", key=f"confirm_no_{skey}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()

            # Mostra último resultado
            last = st.session_state["last_update"].get(skey)
            if last:
                st.markdown("**Último resultado para este lead:**")
                st.json(last)

    # Paginação
    col_a, _, col_c = st.columns(3)
    with col_a:
        if st.button("◀ Página anterior", disabled=current_page <= 1):
            st.session_state.lead_page = max(1, current_page - 1); st.rerun()
    with col_c:
        if st.button("Próxima página ▶", disabled=current_page >= last_page):
            st.session_state.lead_page = min(last_page, current_page + 1); st.rerun()