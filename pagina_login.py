import streamlit as st
import bcrypt
from authlib.integrations.requests_client import OAuth2Session

# ======================
# CONFIG GOOGLE OAUTH
# ======================
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = st.secrets["google_oauth"]["redirect_uri"]

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


# ======================
# GOOGLE CALLBACK
# ======================
def google_callback():
    query_params = st.experimental_get_query_params()

    if "code" not in query_params:
        return

    code = query_params["code"][0]

    oauth = OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope="openid email profile",
        redirect_uri=REDIRECT_URI,
    )

    oauth.fetch_token(TOKEN_URL, code=code)
    userinfo = oauth.get(USERINFO_URL).json()

    st.session_state.google_user = userinfo

    # limpa ?code da URL
    st.experimental_set_query_params()


# ======================
# LOGIN
# ======================
def login(db):
    # ======================
    # INIT STATE (ANTES DE TUDO)
    # ======================
    if "google_user" not in st.session_state:
        st.session_state.google_user = None

    # ======================
    # CALLBACK PRIMEIRO
    # ======================
    google_callback()

    st.image("logo_site.png", use_column_width=True)
    st.title("Login")

    users_collection = db["users"]

    # ======================
    # SE JÁ LOGOU COM GOOGLE
    # ======================
    if st.session_state.google_user:
        email = st.session_state.google_user.get("email")

        user_data = users_collection.find_one({"email": email})

        if not user_data:
            st.error("Seu e-mail não possui acesso ao sistema.")
            st.session_state.google_user = None
            return

        if not user_data.get("ativo", True):
            st.error("Usuário inativado. Contate o administrador.")
            return

        _set_session(user_data)
        st.experimental_rerun()

    # ======================
    # BOTÃO GOOGLE
    # (SÓ SE NÃO HOUVER ?code NA URL)
    # ======================
    query_params = st.experimental_get_query_params()
    if "code" not in query_params:
        oauth = OAuth2Session(
            CLIENT_ID,
            CLIENT_SECRET,
            scope="openid email profile",
            redirect_uri=REDIRECT_URI,
        )
        auth_url, _ = oauth.create_authorization_url(AUTH_URL)
        st.markdown(f"[Entrar com Google]({auth_url})")

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
    # DISCLAIMER
    # ======================
    st.markdown("---")
    with st.expander("ℹ️ Sobre este aplicativo"):
        st.markdown(
            """
            **Finalidade do Aplicativo**

            Plataforma interna de análise de performance comercial,
            com autenticação segura via Google ou login tradicional.
            """
        )

    st.caption("© Century Data — Plataforma interna de análise de performance comercial.")


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
