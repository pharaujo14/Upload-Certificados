import streamlit as st

def pagina_ferramentas(db):

    users_collection = db["ferramentas"]

    if "ferramenta_a_excluir" not in st.session_state:
        st.session_state.ferramenta_a_excluir = None
    if "ferramenta_a_editar" not in st.session_state:
        st.session_state.ferramenta_a_editar = None

    # Dashboard
    st.markdown("<h2 style='text-align:center;'>🛠️ Sistema de Gestão de Ferramentas</h2>", unsafe_allow_html=True)
    ferramentas = list(users_collection.find())
    st.markdown(f"<h4 style='text-align:center;'>Total cadastradas: <span style='color:green;'>{len(ferramentas)}</span></h4>", unsafe_allow_html=True)
    st.markdown("---")

    # Lista de ferramentas
    st.subheader("📋 Ferramentas")
    if ferramentas:
        for ferramenta in ferramentas:
            nome = ferramenta.get('ferramenta') or ferramenta.get('nome', 'Sem Nome')
            with st.container():
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"<div style='padding:8px; border:1px solid #ddd; border-radius:10px;'><b>{nome}</b></div>", unsafe_allow_html=True)
                with col2:
                    if st.button("✏️ Editar", key=f"edit_{ferramenta['_id']}"):
                        st.session_state.ferramenta_a_editar = ferramenta
                with col3:
                    if st.button("🗑️ Excluir", key=f"delete_{ferramenta['_id']}"):
                        st.session_state.ferramenta_a_excluir = ferramenta
    else:
        st.info("Nenhuma ferramenta cadastrada.")

    # Expander de confirmação de exclusão
    if st.session_state.ferramenta_a_excluir:
        with st.expander("⚠️ Confirmar Exclusão"):
            st.warning(f"Deseja excluir a ferramenta **{st.session_state.ferramenta_a_excluir.get('ferramenta', 'Sem Nome')}**?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Confirmar"):
                    users_collection.delete_one({"_id": st.session_state.ferramenta_a_excluir["_id"]})
                    st.success("Ferramenta excluída com sucesso!")
                    st.session_state.ferramenta_a_excluir = None
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.ferramenta_a_excluir = None

    # Expander de edição
    if st.session_state.ferramenta_a_editar:
        with st.expander("✏️ Editar Ferramenta"):
            novo_nome = st.text_input("Novo nome da ferramenta", value=st.session_state.ferramenta_a_editar.get('ferramenta', ''))
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Salvar"):
                    if not novo_nome.strip():
                        st.warning("Nome não pode ser vazio.")
                    elif users_collection.find_one({"ferramenta_lower": novo_nome.strip().lower(), "_id": {"$ne": st.session_state.ferramenta_a_editar["_id"]}}):
                        st.warning("Já existe uma ferramenta com esse nome.")
                    else:
                        users_collection.update_one(
                            {"_id": st.session_state.ferramenta_a_editar["_id"]},
                            {"$set": {"ferramenta": novo_nome.strip(), "ferramenta_lower": novo_nome.strip().lower()}}
                        )
                        st.success("Ferramenta atualizada com sucesso!")
                        st.session_state.ferramenta_a_editar = None
                        st.experimental_rerun()
            with col2:
                if st.button("❌ Cancelar"):
                    st.session_state.ferramenta_a_editar = None

    st.markdown("---")

    # Formulário de adicionar
    st.subheader("➕ Adicionar Nova Ferramenta")
    with st.form("form_nova_ferramenta"):
        ferramenta = st.text_input("Nome da Nova Ferramenta").strip()
        adicionar_button = st.form_submit_button("Adicionar")

    if adicionar_button:
        if not ferramenta:
            st.error("Por favor, insira o nome da ferramenta.")
        else:
            ferramenta_normalizada = ferramenta.lower()
            if users_collection.find_one({"ferramenta_lower": ferramenta_normalizada}):
                st.warning("Essa ferramenta já está cadastrada.")
            else:
                users_collection.insert_one({
                    "ferramenta": ferramenta,
                    "ferramenta_lower": ferramenta_normalizada
                })
                st.success("Ferramenta adicionada com sucesso!")
                st.experimental_rerun()