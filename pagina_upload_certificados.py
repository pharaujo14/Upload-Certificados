import streamlit as st
import os
import uuid

from PIL import Image
from datetime import date
from auxiliar import enviar_resultado, is_file_in_use, upload_to_drive
from conectaBanco import conectaBanco

# Carregar logos
logo_astronauta = Image.open("logo.png")
logo_century = Image.open("logo_site.png")

# Verifica a role do usuário logado
user_role = st.session_state.get('role', '')

# Carregar credenciais do banco de dados
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]

# Conexão com o banco de dados
db = conectaBanco(db_user, db_password)

def pagina_upload(user_name, user_area):
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            st.image(logo_astronauta, width=150)

        with col2:
            st.markdown("<h1 style='text-align: center; color: black;'>Upload de Certificados</h1>", unsafe_allow_html=True)

        with col3:
            st.image(logo_century, width=150)

        # Campos do formulário
        st.write("Preencha as informações abaixo para registrar a certificação:")

        area_certificacao = ['Vendas', 'Pré-Vendas', 'Técnica']
        area_selecionada = st.selectbox('Área da certificação', area_certificacao)

        tipo_certificacao = ['Nova', 'Renovação']
        tipo_selecionada = st.selectbox('Tipo de certificação', tipo_certificacao)

        collection_ferramentas = db["ferramentas"]

        # Consulta das ferramentas
        ferramentas_cursor = collection_ferramentas.find({}, {"_id": 0, "ferramenta": 1})
        ferramenta_certificacao = [f["ferramenta"] for f in ferramentas_cursor]

        # Selectbox
        ferramenta_selecionada = st.selectbox('Ferramenta', ferramenta_certificacao)

        certification_name = st.text_input(
            "Nome da Certificação [Copie e cole aqui exatamente o que estiver no certificado emitido]", 
            placeholder="Copie e cole aqui exatamente o que estiver no certificado emitido"
        )

        certification_date = st.date_input("Data da Certificação", value=date.today())

        uploaded_file = st.file_uploader("Escolha um arquivo", type=["png", "jpg", "jpeg", "pdf"])

        # Botão para Salvar
        if st.button("Salvar Certificação"):
            if not certification_name or not uploaded_file:
                st.warning("Por favor, preencha todos os campos e envie o arquivo.")
            else:
                try:
                    # Salvar arquivo temporariamente
                    file_name = uploaded_file.name
                    file_path = os.path.join("temp", file_name)
                    os.makedirs("temp", exist_ok=True)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    # Gerar um UUID aleatório para o nome do arquivo
                    unique_id = str(uuid.uuid4())
                    custom_name = f"{user_name}_{ferramenta_selecionada}_{certification_name}_{unique_id}"

                    # Fazer upload para o Google Drive
                    folder_id = "1to0AiUISUyUmFjfR_KeRY8SFXDME8nKv"
                    file_id = upload_to_drive(custom_name, file_path, folder_id, custom_name)

                    if not file_id:
                        st.error("Erro ao fazer upload do arquivo para o Google Drive.")
                    else:
                        # Salvar no banco de dados
                        db.insert_one({
                            "user_name": user_name,
                            "user_area": user_area,
                            "area_certificacao": area_selecionada,
                            "tipo_certificacao": tipo_selecionada,
                            "ferramenta_certificacao": ferramenta_selecionada,
                            "certification_name": certification_name,
                            "certification_date": certification_date.strftime("%Y-%m-%d"),
                            "google_drive_file_id": file_id,
                            "file_name": custom_name,  # Salvar o nome personalizado
                        })
                        st.success("Certificação salva com sucesso!")
                        st.balloons()

                        # Envia o email após o download do PDF
                        subject = f"Nova certificação enviada de {user_name}"
                        body = f"O usuário {user_name} realizou o upload do arquivo {custom_name}."

                        # Configurações de email

                        # Define o remetente e o destinatário
                        sender = st.secrets['smtp']['sender']
                        recipient = st.secrets['smtp']['recipient']
                        password = st.secrets['smtp']['password']

                        # Função de envio de email permanece igual
                        enviar_resultado(subject, body, sender, [recipient], password)


                    # Verificar se o arquivo está em uso antes de removê-lo
                    if is_file_in_use(file_path):
                        st.warning(f"O arquivo {file_path} está em uso e não pode ser removido agora.")
                    else:
                        os.remove(file_path)
                except Exception as e:
                    st.error(f"Erro ao salvar certificação: {e}")