import streamlit as st
import bcrypt
import re
import random
import string
import pyperclip

from pymongo import MongoClient

from conectaBanco import conectaBanco

# Função para adicionar um novo usuário ao MongoDB com senha criptografada e função (usado para fins de administração)
def adicionar_usuario():
    # Inicializar session state para senha e estado de cópia
    if "senha_gerada" not in st.session_state:
        st.session_state.senha_gerada = None
    if "senha_copiada" not in st.session_state:
        st.session_state.senha_copiada = False

    # Carregar credenciais do banco de dados
    db_user = st.secrets["database"]["user"]
    db_password = st.secrets["database"]["password"]

    db = conectaBanco(db_user, db_password)
    users_collection = db["users"]

    with st.form("form_novo_usuario"):
        st.write("Adicionar Novo Usuário")
        username = st.text_input("E-mail do Usuário")
        role = st.selectbox("Função", ["user", "admin"])
        area = st.selectbox("Área", ["Comercial", "Operacional"])
        adicionar_button = st.form_submit_button("Adicionar Usuário")

    if adicionar_button:
        # Validação do e-mail
        if not validar_email(username):
            st.warning("O nome de usuário deve ser um e-mail válido.")
        elif users_collection.find_one({"username": username}):
            st.warning("O e-mail já está em uso. Escolha outro.")
        else:
            # Gerar senha automaticamente
            st.session_state.senha_gerada = gerar_senha_automatica()
            st.session_state.senha_copiada = False  # Resetar estado de cópia

            # Formatar o nome a partir do e-mail
            nome_formatado = formatar_nome(username)

            # Criptografar a senha e adicionar o usuário ao banco de dados
            hashed_password = bcrypt.hashpw(st.session_state.senha_gerada.encode("utf-8"), bcrypt.gensalt())
            users_collection.insert_one({
                "username": username,
                "password": hashed_password,
                "role": role,
                "area": area,
                "nome": nome_formatado
            })

            st.success(f"Usuário {username} com função '{role}' adicionado com sucesso!")

    # Exibir a senha gerada (fora do formulário)
    if st.session_state.senha_gerada:
        st.info("Usuário criado com sucesso! Anote a senha gerada:")
        st.text_area("Senha do usuário", value=st.session_state.senha_gerada, height=50, key="senha_texto")
        st.button("Copiar senha", on_click=copiar_senha_callback)

        if st.session_state.senha_copiada:
            st.success("Senha copiada para a área de transferência!")

# Função para troca de senha
def trocar_senha():
    # Carregar credenciais do banco de dados
    db_user = st.secrets["database"]["user"]
    db_password = st.secrets["database"]["password"]

    db = conectaBanco(db_user, db_password)
    users_collection = db["users"]
    username = st.session_state.get('username')

    if not username:
        st.error("Você precisa estar logado para trocar a senha.")
        return

    with st.form("form_trocar_senha"):
        st.write("Troca de Senha")
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_nova_senha = st.text_input("Confirmar Nova Senha", type="password")
        senha_valida = validar_senha(nova_senha) and nova_senha == confirmar_nova_senha

        trocar_button = st.form_submit_button("Alterar Senha")

        if trocar_button:
            user_data = users_collection.find_one({"username": username})
            if user_data:
                if bcrypt.checkpw(senha_atual.encode("utf-8"), user_data["password"]):
                    if senha_valida:
                        nova_senha_hash = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt())
                        users_collection.update_one({"username": username}, {"$set": {"password": nova_senha_hash}})
                        st.success("Senha alterada com sucesso!")
                        st.session_state.mostrar_form_troca_senha = False  # Oculta o formulário após sucesso
                    else:
                        if nova_senha != confirmar_nova_senha:
                            st.warning('As senhas não coincidem.')
                        elif not validar_senha(nova_senha):
                            st.warning('A senha deve conter no mínimo 8 caracteres e conter letra maiúscula, minúscula, número e caractere especial.')
                else:
                    st.error("A senha atual está incorreta.")
            else:
                st.error("Usuário não encontrado.")
                
def validar_senha(senha):
    return (
        len(senha) >= 8 and
        any(c.isupper() for c in senha) and
        any(c.islower() for c in senha) and
        any(c.isdigit() for c in senha) and
        any(not c.isalnum() for c in senha)
    )

def gerar_senha_automatica():
    """
    Gera uma senha forte que inclui:
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    - Comprimento mínimo de 8 caracteres
    """
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    senha = [
        random.choice(string.ascii_uppercase),  # Garantir uma maiúscula
        random.choice(string.ascii_lowercase),  # Garantir uma minúscula
        random.choice(string.digits),           # Garantir um número
        random.choice("!@#$%^&*()-_=+"),        # Garantir um caractere especial
    ]
    senha += random.choices(caracteres, k=8 - len(senha))  # Restante aleatório
    random.shuffle(senha)  # Misturar os caracteres
    return ''.join(senha)

def validar_email(email):
    """
    Verifica se o e-mail é válido.
    """
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

def copiar_senha_callback():
    """
    Callback para copiar a senha gerada para a área de transferência.
    """
    pyperclip.copy(st.session_state.senha_gerada)
    st.session_state.senha_copiada = True

def formatar_nome(email):
    """
    Formata o nome a partir de um e-mail no formato 'nome.sobrenome@dominio.com'.
    """
    nome_sobrenome = email.split('@')[0]  # Pega a parte antes do @
    partes = nome_sobrenome.split('.')    # Divide em partes pelo '.'
    if len(partes) >= 2:
        nome = partes[0].capitalize()    # Capitaliza o primeiro nome
        sobrenome = partes[1].capitalize()  # Capitaliza o sobrenome
        return f"{nome} {sobrenome}"
    return nome_sobrenome.capitalize()  # Caso não tenha sobrenome, usa apenas o nome
