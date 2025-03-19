import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from google.cloud import storage

import io
import os
import ssl
import certifi
import tempfile
from google.auth.transport.requests import Request

# Ignorar verificação SSL globalmente
ssl._create_default_https_context = ssl._create_unverified_context

# Forçar uso do certifi corretamente
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Criar uma sessão de requisição sem verificação de SSL
session = requests.Session()
session.verify = False

# Criar credenciais a partir do Streamlit secrets
credentials = Credentials.from_service_account_info(
    st.secrets["google_cloud"],
    scopes=["https://www.googleapis.com/auth/devstorage.read_write"]
)

# Atualizar token manualmente sem session
request = Request()
if not credentials.valid:
    credentials.refresh(request)

# Criar cliente de armazenamento
client = storage.Client(credentials=credentials)

# Configuração do Google Cloud Storage
GCS_BUCKET_NAME = "cookies-c4"

API_UPLOAD_URL = f"https://storage.googleapis.com/upload/storage/v1/b/{GCS_BUCKET_NAME}/o?uploadType=resumable"

# Carregar credenciais da API do arquivo secrets.toml
ORGANIZATIONS = {
    "property": {
        "x-api-key": st.secrets["api"]["property_api_key"],
        "x-api-secret": st.secrets["api"]["property_api_secret"],
        "x-org-id": st.secrets["api"]["property_org_id"]
    },
    "carrefour": {
        "x-api-key": st.secrets["api"]["carrefour_api_key"],
        "x-api-secret": st.secrets["api"]["carrefour_api_secret"],
        "x-org-id": st.secrets["api"]["carrefour_org_id"]
    },
    "sams": {
        "x-api-key": st.secrets["api"]["sams_api_key"],
        "x-api-secret": st.secrets["api"]["sams_api_secret"],
        "x-org-id": st.secrets["api"]["sams_org_id"]
    },
    "cci": {
        "x-api-key": st.secrets["api"]["cci_api_key"],
        "x-api-secret": st.secrets["api"]["cci_api_secret"],
        "x-org-id": st.secrets["api"]["cci_org_id"]
    }
}

API_URL = "https://app.securiti.ai/reporting/v1/sources/query?ref=getCmpCookieConsentRecords"

def fetch_cookie_data(start_date, end_date):
    """Baixa dados de cookies para um intervalo de tempo específico."""
    all_data = []
    start_ts = int(start_date.timestamp())
    end_ts = int(end_date.timestamp())
    
    for org_name, credentials in ORGANIZATIONS.items():
        offset = 0
        while True:
            headers = {
                "x-tident": st.secrets["api"]["x_tident"],
                "x-api-key": credentials["x-api-key"],
                "x-api-secret": credentials["x-api-secret"],
                "x-org-id": credentials["x-org-id"]
            }
            payload = {
                "source": "category_consents_flat",
                "response_config": {"format": 1},
                "pagination": {"type": "limit-offset", "offset": offset, "limit": 100000, "omit_total": True},
                "fields": [],
                "order_by": ["-activity_timestamp"],
                "skip_cache": True,
                "filter": {
                    "op": "and",
                    "value": [
                        {"op": "gte", "field": "activity_timestamp", "value": start_ts},
                        {"op": "lte", "field": "activity_timestamp", "value": end_ts}
                    ]
                }
            }
            
            response = session.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                records = data.get("data", [])
                if not records:
                    break
                for record in records:
                    record["organization"] = org_name
                all_data.extend(records)
                offset += 100000
            else:
                st.error(f"Erro ao buscar dados para {org_name}: {response.status_code}")
                break
    
    return pd.DataFrame(all_data)

def upload_parquet_gcs(df, filename):
    """Faz upload de um DataFrame como Parquet no Google Cloud Storage (GCS)."""
    try:
        output = io.BytesIO()
        df.to_parquet(output, engine="pyarrow")
        output.seek(0)
        blob = client.bucket(GCS_BUCKET_NAME).blob(filename)
        blob.upload_from_file(output, content_type="application/octet-stream")
        st.write(f"📤 Arquivo {filename} enviado para GCS!")
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Google Cloud Storage: {e}")

def preencher_dias_faltantes():
    """Verifica se há arquivos ausentes no Google Cloud Storage e baixa os dados necessários."""
    data_atual = datetime.now()
    data_inicio = datetime(2024, 3, 1)
    dias_faltantes = []

    existing_blobs = {blob.name for blob in client.bucket(GCS_BUCKET_NAME).list_blobs(timeout=300)}

    while data_inicio < data_atual:
        filename = f"cookies_{data_inicio.strftime('%Y-%m-%d')}.parquet"
        if filename not in existing_blobs:
            dias_faltantes.append(data_inicio)
        data_inicio += timedelta(days=1)

    for dia in dias_faltantes:
        df = fetch_cookie_data(dia, dia + timedelta(days=1))
        if not df.empty:
            upload_parquet_gcs(df, f"cookies_{dia.strftime('%Y-%m-%d')}.parquet")
        else:
            st.write(f"⚠️ Nenhum dado encontrado para {dia.strftime('%Y-%m-%d')}")

# Executar a verificação automática após meia-noite
if datetime.now().hour >= 0:
    preencher_dias_faltantes()