import streamlit as st
import bcrypt

from utils.auxiliar import validar_email, formatar_nome, gerar_senha_automatica
from utils.email_utils import gerar_email_institucional, enviar_resultado

def badge(text, color):
    return f"<span style='background:{color}; color:white; padding:3px 8px; border-radius:8px; font-size:11px;'>{text}</span>"

def gerenciar_usuarios(db):
    
    criar_usuario(db)

    users_collection = db["users"]

    if "usuario_a_editar" not in st.session_state:
        st.session_state.usuario_a_editar = None

    st.markdown("<h2 style='text-align:center;'>👥 Gestão de Usuários</h2>", unsafe_allow_html=True)

    # Campo de busca
    busca = st.text_input("🔎 Buscar usuário por nome ou e-mail").strip().lower()

    usuarios = list(users_collection.find())

    if busca:
        usuarios = [u for u in usuarios if busca in u.get("nome", "").lower() or busca in u.get("username", "").lower()]

    st.markdown(f"**Total encontrados:** {len(usuarios)}")

    st.markdown("---")

    st.subheader("📑 Lista de Usuários")

    if usuarios:
        for usuario in usuarios:
            ativo = usuario.get("ativo", True)
            badge_status = badge("Ativo", "#28a745") if ativo else badge("Inativo", "#dc3545")
            badge_role = badge(usuario.get("role", "user").capitalize(), "#007bff")
            badge_area = badge(usuario.get("area", ""), "#17a2b8")

            with st.container():
                st.markdown(
                    f"""
                    <div style='border:1px solid #ddd; border-radius:10px; padding:10px; margin-bottom:10px;'>
                        <b>Nome:</b> {usuario.get('nome', '')} <br>
                        <b>E-mail:</b> {usuario.get('username', '')} <br>
                        {badge_status} {badge_role} {badge_area}
                    </div>
                    """, unsafe_allow_html=True
                )
                
                col1, col2, col3 = st.columns([1,1,1])

                with col1:
                    if st.button("✏️ Editar", key=f"editar_{usuario['_id']}"):
                        st.session_state.usuario_a_editar = usuario

                with col2:
                    if st.button("🚩 Inativar" if ativo else "✅ Reativar", key=f"inativar_{usuario['_id']}"):
                        users_collection.update_one(
                            {"_id": usuario["_id"]},
                            {"$set": {"ativo": not ativo}}
                        )
                        st.success("Status do usuário atualizado.")
                        st.experimental_rerun()

                with col3:
                    if st.button("🔑 Resetar Senha", key=f"reset_{usuario['_id']}"):
                        nova_senha = gerar_senha_automatica()
                        hashed_password = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt())
                        users_collection.update_one(
                            {"_id": usuario["_id"]},
                            {"$set": {"password": hashed_password}}
                        )

                        body = gerar_email_institucional("redefinir_senha", {
                            "nome": usuario.get("nome", ""),
                            "senha": nova_senha,
                            "link_sistema": "https://centurydata.streamlit.app/"
                        })

                        subject = "🔑 Redefinição de senha - Century Data"
                        sender = st.secrets['smtp']['sender']
                        recipient = usuario.get("username", "")
                        password_smtp = st.secrets['smtp']['password']

                        enviar_resultado(subject, body, sender, [recipient], password_smtp, html=True)

                        st.success("Senha redefinida e enviada por e-mail.")
    else:
        st.info("Nenhum usuário encontrado.")

    # Formulário de edição
    if st.session_state.usuario_a_editar:
        usuario = st.session_state.usuario_a_editar
        with st.expander(f"✏️ Editar usuário: {usuario.get('username', '')}", expanded=True):
            novo_nome = st.text_input("Nome", value=usuario.get("nome", ""))
            novo_email = st.text_input("E-mail", value=usuario.get("username", ""))
            nova_role = st.selectbox("Função", ["user", "admin", "viewer", "bdr", "account", "prevendas"], index=["user", "admin", "viewer", "bdr", "account", "prevendas"].index(usuario.get("role", "user")))
            nova_area = st.selectbox("Área", ["Comercial", "Operacional"], index=["Comercial", "Operacional"].index(usuario.get("area", "Comercial")))

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar alterações"):
                    if not validar_email(novo_email):
                        st.warning("E-mail inválido.")
                    elif novo_email != usuario.get("username") and users_collection.find_one({"username": novo_email}):
                        st.warning("Este e-mail já está em uso.")
                    else:
                        users_collection.update_one(
                            {"_id": usuario["_id"]},
                            {"$set": {
                                "nome": novo_nome.strip(),
                                "username": novo_email.strip(),
                                "role": nova_role,
                                "area": nova_area
                            }}
                        )
                        st.success("Usuário atualizado com sucesso!")
                        st.session_state.usuario_a_editar = None
                        st.experimental_rerun()
            with col2:
                if st.button("❌ Cancelar edição"):
                    st.session_state.usuario_a_editar = None

    st.markdown("---")

def criar_usuario(db):

    users_collection = db["users"]

    st.subheader("➕ Adicionar Novo Usuário")

    with st.form("form_novo_usuario"):
        username = st.text_input("E-mail do Usuário")
        role = st.selectbox("Função", ["user", "admin", "viewer", "bdr", "account", "prevendas"])
        area = st.selectbox("Área", ["Comercial", "Operacional"])
        adicionar_button = st.form_submit_button("Adicionar Usuário")

    if adicionar_button:
        if not validar_email(username):
            st.warning("O e-mail não é válido.")
        elif users_collection.find_one({"username": username}):
            st.warning("O e-mail já está em uso.")
        else:
            senha_gerada = gerar_senha_automatica()
            nome_formatado = formatar_nome(username)
            hashed_password = bcrypt.hashpw(senha_gerada.encode("utf-8"), bcrypt.gensalt())

            users_collection.insert_one({
                "username": username,
                "password": hashed_password,
                "role": role,
                "area": area,
                "nome": nome_formatado,
                "ativo": True
            })

            # Gerar e-mail institucional
            body = gerar_email_institucional("criar_usuario", {
                "nome": nome_formatado,
                "username": username,
                "senha": senha_gerada,
                "link_sistema": "https://centurydata.streamlit.app/"
            })

            subject = "Seus dados de acesso - Century Data"
            sender = st.secrets['smtp']['sender']
            recipient = username
            password = st.secrets['smtp']['password']

            enviar_resultado(subject, body, sender, [recipient], password, html=True)

            st.success(f"Usuário {username} criado e senha enviada por e-mail!")