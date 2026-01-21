import streamlit as st
import bcrypt

# Função para autenticação
def login(db):
    st.image("logo_site.png", use_column_width=True)

    st.title("Login")

    login_form = st.form(key="login_form")
    username = login_form.text_input("Usuário")
    password = login_form.text_input("Senha", type="password")
    login_button = login_form.form_submit_button("Entrar")

    if login_button:
        users_collection = db["users"]
        user_data = users_collection.find_one({"username": username})

        if user_data:
            if not user_data.get("ativo", True):
                st.error("Usuário inativado. Contate o administrador.")
            elif bcrypt.checkpw(password.encode("utf-8"), user_data["password"]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.session_state['role'] = user_data["role"]
                st.session_state['area'] = user_data["area"]
                st.session_state['nome'] = user_data["nome"]
                st.success(f"Bem-vindo, {username}!")
                st.experimental_rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        else:
            st.error("Usuário ou senha incorretos.")

# Função para verificar se o usuário está autenticado
def is_authenticated():
    return st.session_state.get('logged_in', False)