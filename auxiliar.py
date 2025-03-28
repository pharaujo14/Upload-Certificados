import psutil
import smtplib
import streamlit as st
import requests
import re
import random
import string
import pyperclip

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
    try:
        pyperclip.copy(st.session_state.senha_gerada)
        st.session_state.senha_copiada = True
    except pyperclip.PyperclipException:
        st.warning("Não foi possível copiar automaticamente para a área de transferência. Copie manualmente a senha exibida acima.")

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
