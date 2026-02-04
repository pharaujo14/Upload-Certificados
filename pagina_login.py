import streamlit as st
import bcrypt
from streamlit_google_auth import Authenticate


def login(db):
    st.image("logo_site.png", use_column_width=True)
    st.title("Login")

    # ======================
    # LOGIN COM GOOGLE
    # ======================
    auth = Authenticate(
        secret_credentials_path=".streamlit/secrets.toml",
        cookie_name="google_auth",
        cookie_key="random_cookie_key",
        redirect_uri="http://localhost:8501"
    )

    auth_info = auth.login("Entrar com Google", "main")

    if auth_info:
        email = auth_info["email"]

        users_collection = db["users"]
        user_data = users_collection.find_one({"email": email})

        if not user_data:
            st.error("Seu e-mail não possui acesso ao sistema.")
            auth.logout("Logout", "sidebar")
            return

        if not user_data.get("ativo", True):
            st.error("Usuário inativado. Contate o administrador.")
            return

        # Login OK
        st.session_state["logged_in"] = True
        st.session_state["username"] = user_data["username"]
        st.session_state["role"] = user_data["role"]
        st.session_state["area"] = user_data["area"]
        st.session_state["nome"] = user_data["nome"]

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
        users_collection = db["users"]
        user_data = users_collection.find_one({"username": username})

        if user_data:
            if not user_data.get("ativo", True):
                st.error("Usuário inativado. Contate o administrador.")
            elif bcrypt.checkpw(password.encode("utf-8"), user_data["password"]):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = user_data["role"]
                st.session_state["area"] = user_data["area"]
                st.session_state["nome"] = user_data["nome"]
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.error("Usuário ou senha incorretos.")
