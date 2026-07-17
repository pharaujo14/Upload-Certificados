import streamlit as st
import pytz

from PIL import Image

from utils.conectaBanco import conectaBanco
from pagina_login import login, is_authenticated

from pagina_usuarios import gerenciar_usuarios
from pagina_ferramentas import pagina_ferramentas
from pagina_upload_certificados import pagina_upload
from pagina_relatorios import pagina_relatorios
from pagina_relatorios_bdr_executivo import pagina_relatorios_bdr_executivo
from pagina_relatorios_bdr_operacional import pagina_relatorios_bdr_operacional
from pagina_upload_leads import pagina_upload_leads
from pagina_busca_leads import pagina_busca_leads

# ======================
# Configurações iniciais
# ======================
timezone_brasil = pytz.timezone("America/Sao_Paulo")

st.set_page_config(
    page_title="Century Data",
    page_icon="Century_mini_logo-32x32.png",
    layout="wide"
)

# ======================
# Sessão do usuário
# ======================
user_role = st.session_state.get("role", "")
user_name = st.session_state.get("nome", "")
user_area = st.session_state.get("area", "")

# ======================
# Banco de dados
# ======================
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]
db = conectaBanco(db_user, db_password)

# ======================
# Autenticação
# ======================
if not is_authenticated():
    login(db)
    st.stop()

# ======================
# Logos
# ======================
logo_astronauta = Image.open("logo.png")
logo_century = Image.open("logo_site.png")


# ======================
# SIDEBAR - MENU INLINE
# ======================
with st.sidebar:
    st.image(logo_century, width=150)
    st.markdown("### ☰ Menu Principal")

    # -------- BDRs --------
    if user_role in ["viewer", "admin", "bdr"]:
        with st.expander("📊 BDRs", expanded=True):
            if st.button("Dashboard", use_container_width=True, key="btn_bdr_dashboard"):
                st.session_state["page"] = "bdr_dashboard"
                
    # -------- Leads --------
    if user_role in ["admin"]:
        with st.expander("📈 Leads", expanded=True):
            if st.button("Fazer upload", use_container_width=True, key="btn_leads_upload"):
                st.session_state["page"] = "leads"
                
            if st.button("Consultar leads", use_container_width=True, key="btn_leads_search"):
                st.session_state["page"] = "search_leads"

    # ----- Certificados -----
    with st.expander("📁 Certificados"):
        if st.button("Fazer upload", use_container_width=True, key="btn_cert_upload"):
            st.session_state["page"] = "upload"
            
        if user_role in ["viewer", "admin"]:
            if st.button("Relatórios", use_container_width=True, key="btn_cert_relatorios"):
                st.session_state["page"] = "relatorios_certificados"

        if user_role == "admin":
            if st.button("Controle de Ferramentas", use_container_width=True, key="btn_cert_ferramentas"):
                st.session_state["page"] = "ferramentas"
                
    # ----- Calculadora -----
    if user_role in ["viewer", "admin", "account", "prevendas"]:
        with st.expander("🧮 Calculadora"):
            st.link_button(
                "Abrir calculadora de preço",
                "https://precovendas.streamlit.app/", use_container_width=True
            )

    # ----- DocEase -----
    with st.expander("🤑 Envio de NF / Reembolso"):
        st.link_button(
            "Abrir DocEase",
            "https://docease.streamlit.app/", use_container_width=True
        )

    # ---- Configurações ----
    if user_role == "admin":
        with st.expander("⚙️ Configurações"):
            if st.button("Controle de usuários", use_container_width=True, key="btn_config_usuarios"):
                st.session_state["page"] = "usuarios"
                
# ======================
# ROTEAMENTO
# ======================
if "page" not in st.session_state:
    if user_role in ["admin", "viewer", "bdr"]:
        st.session_state["page"] = "bdr_dashboard"
    else:
        st.session_state["page"] = "upload"

page = st.session_state["page"]
    
# -------- BDRs --------
if page == "bdr_dashboard":
    if user_role in ["viewer", "admin"]:
        pagina_relatorios_bdr_executivo(db)
    else:
        pagina_relatorios_bdr_operacional(db)

# -------- Leads --------
elif page == "leads":
    if user_role in ["viewer", "admin"]:
        pagina_upload_leads(db)
    else:
        st.warning("Você não tem permissão para acessar esta aba.")
        
elif page == "search_leads":
    if user_role in ["viewer", "admin"]:
        pagina_busca_leads(db)
    else:
        st.warning("Você não tem permissão para acessar esta aba.")
        
# ----- Certificados -----
elif page == "upload":
    pagina_upload(user_name, user_area)

elif page == "relatorios_certificados":
    if user_role in ["viewer", "admin"]:
        pagina_relatorios(db)
    else:
        st.warning("Você não tem permissão para acessar esta aba.")

elif page == "ferramentas":
    if user_role == "admin":
        pagina_ferramentas(db)
    else:
        st.warning("Você não tem permissão para acessar esta aba.")

elif page == "usuarios":
    if user_role == "admin":
        gerenciar_usuarios(db)
    else:
        st.warning("Você não tem permissão para acessar esta aba.")
