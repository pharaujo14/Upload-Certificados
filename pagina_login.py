import streamlit as st
import bcrypt
import json
import os
from streamlit_google_auth import Authenticate
import tempfile
import os

GOOGLE_SECRET_FILE = os.path.join(
    tempfile.gettempdir(),
    "google_oauth_client.json"
)


def _ensure_google_oauth_file():
    """
    Cria o arquivo JSON de credenciais do Google OAuth
    a partir do secrets.toml (se ainda não existir).
    """
    google_oauth = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]],
        }
    }

    with open(GOOGLE_SECRET_FILE, "w") as f:
        json.dump(google_oauth, f)

    return GOOGLE_SECRET_FILE


# ======================
# LOGIN
# ======================
def login(db):
    st.image("logo_site.png", use_column_width=True)
    st.title("Login")

    users_collection = db["users"]

    # ======================
    # LOGIN COM GOOGLE (SSO)
    # ======================
    secret_file = _ensure_google_oauth_file()
    redirect_uri = st.secrets["google_oauth"]["redirect_uri"]

    auth = Authenticate(
        secret_credentials_path=secret_file,
        redirect_uri=redirect_uri,
        cookie_name="google_auth",
        cookie_key="random_cookie_key",
    )

    auth_info = auth.login("Entrar com Google", "main")

    if auth_info:
        email = auth_info.get("email")

        user_data = users_collection.find_one({"email": email})

        if not user_data:
            st.error("Seu e-mail não possui acesso ao sistema.")
            auth.logout("Logout", "sidebar")
            return

        if not user_data.get("ativo", True):
            st.error("Usuário inativado. Contate o administrador.")
            return

        _set_session(user_data)
        st.experimental_rerun()

    st.markdown("---")

    # ======================
    # LOGIN TRADICIONAL
    # ======================
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        user_data = users_collection.find_one({"username": username})

        if not user_data:
            st.error("Usuário ou senha incorretos.")
            return

        if not user_data.get("ativo", True):
            st.error("Usuário inativado. Contate o administrador.")
            return

        if not bcrypt.checkpw(password.encode(), user_data["password"]):
            st.error("Usuário ou senha incorretos.")
            return

        _set_session(user_data)
        st.experimental_rerun()


    # ======================
    # DISCLAIMER (discreto)
    # ======================
    st.markdown("---")

    with st.expander("ℹ️ Sobre este aplicativo"):
        st.markdown(
            """
            **Finalidade do Aplicativo**

            Este aplicativo foi desenvolvido para **análise de performance comercial e gestão de resultados**, 
            com foco em **equipes de vendas, BDRs e operações comerciais (RevOps)**.

            A plataforma permite:
            - Acompanhar métricas de desempenho ao longo do tempo  
            - Calcular scores de performance normalizados  
            - Visualizar indicadores de produtividade, eficiência e resultados comerciais  
            - Apoiar decisões estratégicas com base em dados consolidados  

            **Uso do Login com Google**

            O login com Google é utilizado **exclusivamente para autenticação segura**, permitindo:
            - Identificação individual do usuário  
            - Acesso personalizado a dados e relatórios  
            - Proteção das informações e controle de acesso  

            Nenhuma informação pessoal é utilizada para fins publicitários ou compartilhada com terceiros.  
            Os dados obtidos por meio da autenticação são usados **somente para funcionamento interno do aplicativo**.

            **Público-alvo**
            - Profissionais de vendas  
            - Líderes comerciais  
            - Gestores de RevOps  
            - Analistas de performance e operações
            """
        )

    st.caption(
        "© Century Data — Plataforma interna de análise de performance comercial."
    )

# ======================
# SESSION HELPERS
# ======================
def _set_session(user_data):
    st.session_state["logged_in"] = True
    st.session_state["username"] = user_data.get("username")
    st.session_state["nome"] = user_data.get("nome")
    st.session_state["role"] = user_data.get("role")
    st.session_state["area"] = user_data.get("area")


def is_authenticated():
    return st.session_state.get("logged_in", False)
