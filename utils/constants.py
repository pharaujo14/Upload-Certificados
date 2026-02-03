"""
Constantes globais da aplicacao.
"""

# Google Sheets
SHEET_ID = "1a1pjExKkW8yP6Gla9XdjvfDZmw2cfVomQzHeGfR2H_g"
SHEET_TAB = "KPIs"

# Schema obrigatorio da aba KPIs
EXPECTED_COLUMNS = [
    "BDR",
    "Semana 1º contato",
    "Mês",
    "Ano",
    "Novos Leads",
    "Leads Reengajamento",
    "Total Leads",
    "Resposta Positivo WhatsApp",
    "Resposta Negativa WhatsApp",
    "Resposta Positivo Ligacao",
    "Resposta Negativa Ligacao",
    "Resposta Positivo E-mail",
    "Resposta Negativa E-mail",
    "Total positivas",
    "Total Negativas",
    "Reuniao Agendada",
    "Reuniao Aguardando",
    "Reuniao Realizada",
    "Pipeline",
    "PoC",
    "Proposta Enviadas",
    "Propostas Aceitas",
    "Propostas Recusadas",
    "Booking TCV",
]

# Perfis de usuario
PROFILE_ADMIN = "admin"
PROFILE_BDR = "bdr"
VALID_PROFILES = [PROFILE_ADMIN, PROFILE_BDR]

# Cache
CACHE_TTL_SECONDS = 300  # 5 minutos

# Banco de dados
DB_PATH = "database/users.db"

