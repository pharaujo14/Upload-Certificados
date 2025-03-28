import streamlit as st
import bcrypt

from auxiliar import validar_email, formatar_nome, gerar_senha_automatica, copiar_senha_callback

def badge(text, color):
    return f"<span style='background:{color}; color:white; padding:3px 8px; border-radius:8px; font-size:11px;'>{text}</span>"

def gerenciar_usuarios(db):

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
                col1, col2 = st.columns([1,1])
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
    else:
        st.info("Nenhum usuário encontrado.")

    # Formulário de edição
    if st.session_state.usuario_a_editar:
        usuario = st.session_state.usuario_a_editar
        with st.expander(f"✏️ Editar usuário: {usuario.get('username', '')}", expanded=True):
            novo_nome = st.text_input("Nome", value=usuario.get("nome", ""))
            novo_email = st.text_input("E-mail", value=usuario.get("username", ""))
            nova_role = st.selectbox("Função", ["user", "admin", "viewer"], index=["user", "admin", "viewer"].index(usuario.get("role", "user")))
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

    # Formulário de adição
    st.subheader("➕ Adicionar Novo Usuário")

    if "senha_gerada" not in st.session_state:
        st.session_state.senha_gerada = None
    if "senha_copiada" not in st.session_state:
        st.session_state.senha_copiada = False

    with st.form("form_novo_usuario"):
        username = st.text_input("E-mail do Usuário")
        role = st.selectbox("Função", ["user", "admin", "viewer"])
        area = st.selectbox("Área", ["Comercial", "Operacional"])
        adicionar_button = st.form_submit_button("Adicionar Usuário")

    if adicionar_button:
        if not validar_email(username):
            st.warning("O e-mail não é válido.")
        elif users_collection.find_one({"username": username}):
            st.warning("O e-mail já está em uso.")
        else:
            st.session_state.senha_gerada = gerar_senha_automatica()
            st.session_state.senha_copiada = False

            nome_formatado = formatar_nome(username)

            hashed_password = bcrypt.hashpw(st.session_state.senha_gerada.encode("utf-8"), bcrypt.gensalt())
            users_collection.insert_one({
                "username": username,
                "password": hashed_password,
                "role": role,
                "area": area,
                "nome": nome_formatado,
                "ativo": True
            })
            st.success(f"Usuário {username} criado com sucesso!")

    if st.session_state.senha_gerada:
        st.info("Usuário criado! Anote a senha:")
        st.text_area("Senha gerada", value=st.session_state.senha_gerada, height=50, key="senha_texto")
        st.button("Copiar senha", on_click=copiar_senha_callback)

        if st.session_state.senha_copiada:
            st.success("Senha copiada para a área de transferência!")