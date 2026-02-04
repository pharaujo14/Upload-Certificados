import streamlit as st
import bcrypt
from streamlit_google_auth import Authenticate


def login(db):
    st.image("logo_site.png", use_column_width=True)
    st.title("Login")

    users_collection = db["users"]

    # ======================
    # LOGIN COM GOOGLE (SSO)
    # ======================
    google_creds = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["https://centurydata.streamlit.app/"],
        }
    }

    auth = Authenticate(
        credentials=google_creds,
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


def _set_session(user_data):
    st.session_state["logged_in"] = True
    st.session_state["username"] = user_data.get("username")
    st.session_state["nome"] = user_data.get("nome")
    st.session_state["role"] = user_data.get("role")
    st.session_state["area"] = user_data.get("area")


def is_authenticated():
    return st.session_state.get("logged_in", False)
