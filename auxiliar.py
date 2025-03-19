import psutil
import smtplib
import streamlit as st
import requests

from email.mime.text import MIMEText
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request

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
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.content.decode()}")

        if response.status_code not in [200, 201]:
            st.error(f"Erro ao inicializar o upload: {response.content.decode()}")
            return None

        # URL de upload retornada pelo Google
        upload_url = response.headers["Location"]
        if not upload_url:
            print("Erro: URL de upload não encontrada no cabeçalho.")
            return

        # Upload do arquivo
        with open(file_path, "rb") as f:
            upload_response = session.put(upload_url, headers={"Content-Type": "application/octet-stream"}, data=f)
            print(f"Upload Response Status: {upload_response.status_code}")
            print(f"Upload Response Content: {upload_response.content.decode()}")

        if upload_response.status_code in [200, 201]:
            file_id = upload_response.json().get("id")
            return file_id
        else:
            st.error(f"Erro ao fazer upload do arquivo: {upload_response.content.decode()}")
            return None
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Google Drive: {e}")
        return None