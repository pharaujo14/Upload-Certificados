import streamlit as st
import pytz

from PIL import Image

from conectaBanco import conectaBanco
from login import login, is_authenticated
from cadastra_user import trocar_senha, adicionar_usuario
from streamlit_option_menu import option_menu
from upload_certificados import pagina_upload
from relatorios import pagina_relatorios

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


# Filtros e seleção de período
with st.sidebar:
    st.image(logo_century, width=150)

    # Determinar opções do menu com base na role
    menu_options = ["Upload de Certificados", "Trocar Senha"]
    menu_icons = ["upload", "key"]

    if user_role in ["viewer", "admin"]:
        menu_options.append("Relatórios")
        menu_icons.append("bar-chart")

    if user_role == "admin":
        menu_options.append("Cadastrar Novo Usuário")
        menu_icons.append("person-plus")

    # Configuração do menu dinâmico
    selected_tab = option_menu(
        menu_title="Menu Principal",
        options=menu_options,
        icons=menu_icons,
        menu_icon="list",
        default_index=0,
    )

# Aba de Upload de Certificados
if selected_tab == "Upload de Certificados":
    pagina_upload()
    
# Aba de Relatórios
elif selected_tab == "Relatórios":
    if user_role in ["viewer", "admin"]:
        pagina_relatorios()
    else:
        st.warning("Você não tem permissão para acessar esta aba.")

# Aba de Relatórios
elif selected_tab == "Trocar Senha":
    st.markdown("<h2>Trocar senha</h2>", unsafe_allow_html=True)
    trocar_senha()

# Aba de Relatórios
elif selected_tab == "Cadastrar Novo Usuário":
    st.markdown("<h2>Cadastrar Novo usuário</h2>", unsafe_allow_html=True)
    if user_role in ["admin"]:
        adicionar_usuario()
    else:
        st.warning("Você não tem permissão para acessar esta aba.")
