import streamlit as st
import bcrypt
from streamlit_google_auth import Authenticate


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
    auth = Authenticate(
        secret_credentials_path=".streamlit/secrets.toml",
        cookie_name="google_auth",
        cookie_key="random_cookie_key",
        redirect_uri="https://centurydata.streamlit.app/",
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
    with st.form(key="login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar")

    if login_button:
        user_data = users_collection.find_one({"username": username})

        if not user_data:
            st.error("Usuário ou senha incorretos.")
            return

        if not user_data.get("ativo", True):
            st.error("Usuário inativado. Contate o administrador.")
            return

        if not bcrypt.checkpw(password.encode("utf-8"), user_data["password"]):
            st.error("Usuário ou senha incorretos.")
            return

        _set_session(user_data)
        st.experimental_rerun()


# ======================
# SESSION HELPERS
# ======================
def _set_session(user_data: dict):
    st.session_state["logged_in"] = True
    st.session_state["username"] = user_data.get("username")
    st.session_state["nome"] = user_data.get("nome")
    st.session_state["role"] = user_data.get("role")
    st.session_state["area"] = user_data.get("area")


# ======================
# AUTH CHECK
# ======================
def is_authenticated():
    return st.session_state.get("logged_in", False)
