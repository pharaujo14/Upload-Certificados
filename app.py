import os
import requests
import streamlit as st
import pytz
import psutil
import uuid
import smtplib

from PIL import Image
from datetime import date

from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

from conectaBanco import conectaBanco
from login import login, is_authenticated
from cadastra_user import trocar_senha, adicionar_usuario

# Função para envio de email
def enviar_resultado(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    
    print("Email enviado com sucesso!")

# Função para verificar se o arquivo está em uso
def is_file_in_use(file_path):
    for proc in psutil.process_iter(['open_files']):
        try:
            for file in proc.info['open_files'] or []:
                if file.path == file_path:
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False

# Configuração da Conta de Serviço para o Google Drive
def upload_to_drive(file_name, file_path, folder_id, custom_name):
    try:
        # Carregar as credenciais do `secrets.toml`
        credentials = Credentials.from_service_account_info(
            st.secrets["google_drive"],
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Atualizar o token manualmente
        session = requests.Session()
        session.verify = False  # Ignorar verificação de certificado SSL
        request = Request(session=session)
        if not credentials.valid:
            credentials.refresh(request)

        # URL do Google Drive para upload
        url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable"
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }

        # Configuração dos metadados do arquivo
        metadata = {
            "name": custom_name,
            "parents": [folder_id]
        }
        response = session.post(url, headers=headers, json=metadata)
        if response.status_code not in [200, 201]:
            st.error(f"Erro ao inicializar o upload: {response.content.decode()}")
            return None

        # URL de upload retornada pelo Google
        upload_url = response.headers["Location"]

        # Upload do arquivo
        with open(file_path, "rb") as f:
            upload_response = session.put(upload_url, headers={"Content-Type": "application/octet-stream"}, data=f)

        if upload_response.status_code in [200, 201]:
            file_id = upload_response.json().get("id")
            return file_id
        else:
            st.error(f"Erro ao fazer upload do arquivo: {upload_response.content.decode()}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Google Drive: {e}")
        return None
        
# Definir o timezone do Brasil
timezone_brasil = pytz.timezone('America/Sao_Paulo')

# Verifica se o usuário está autenticado
if not is_authenticated():
    login()
    st.stop()

# Verifica a role do usuário logado
user_role = st.session_state.get('role', '')
user_name = st.session_state.get('nome', '')
user_area = st.session_state.get('area', '')

# Carregar credenciais do banco de dados
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]

# Conexão com o banco de dados
db = conectaBanco(db_user, db_password)

# Carregar logos
logo_astronauta = Image.open("logo.png")
logo_century = Image.open("logo_site.png")

# Configurações da página com o logo
st.set_page_config(page_title="Century Data", page_icon="Century_mini_logo-32x32.png", layout="wide")

# Layout da página
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.image(logo_astronauta, width=150)

with col2:
    st.markdown("<h1 style='text-align: center; color: black;'>Upload de Certificados</h1>", unsafe_allow_html=True)

with col3:
    st.image(logo_century, width=150)

# Filtros e seleção de período
with st.sidebar:
    st.image(logo_century, width=150)

    if 'mostrar_form_troca_senha' not in st.session_state:
        st.session_state.mostrar_form_troca_senha = False

    if st.button("Trocar Senha"):
        st.session_state.mostrar_form_troca_senha = not st.session_state.mostrar_form_troca_senha

    if st.session_state.mostrar_form_troca_senha:
        trocar_senha()

    if user_role == "admin":
        if 'mostrar_form_criar_user' not in st.session_state:
            st.session_state.mostrar_form_criar_user = False

        if st.button("Novo usuário"):
            st.session_state.mostrar_form_criar_user = not st.session_state.mostrar_form_criar_user

        if st.session_state.mostrar_form_criar_user:
            adicionar_usuario()

# Campos do formulário
st.write("Preencha as informações abaixo para registrar a certificação:")

area_certificacao = ['Vendas', 'Pré-Vendas', 'Técnica']
area_selecionada = st.selectbox('Área da certificação', area_certificacao)

tipo_certificacao = ['Nova', 'Renovação']
tipo_selecionada = st.selectbox('Tipo de certificação', tipo_certificacao)

ferramenta_certificacao = ['BigID', 'Noname', 'Akamai', 'OneTrust', 'SentinelOne', 'Zendesk', 'Securiti', 'AppGate', 'IBM', 'Zscaler', 'Wiz', 'Thales']
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
            folder_id = "1Iy2It2zBXi7O_Ict3rDy7HH_kllb7xc2"
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
