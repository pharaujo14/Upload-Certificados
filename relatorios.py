import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from PIL import Image
from conectaBanco import conectaBanco

# Carregar logos
logo_astronauta = Image.open("logo.png")
logo_century = Image.open("logo_site.png")

# Verifica a role do usuário logado
user_role = st.session_state.get('role', '')
user_name = st.session_state.get('nome', '')
user_area = st.session_state.get('area', '')

# Carregar credenciais do banco de dados
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]

# Conexão com o banco de dados
db = conectaBanco(db_user, db_password)

def pagina_relatorios():
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        st.image(logo_astronauta, width=150)

    with col2:
        st.markdown("<h1 style='text-align: center; color: black;'>Relatórios</h1>", unsafe_allow_html=True)

    with col3:
        st.image(logo_century, width=150)

    # Conectar ao banco e buscar dados
    try:
        data = list(db.find())  # Buscar todos os registros do banco
        df = pd.DataFrame(data)  # Converter para DataFrame

        # Filtros
        with st.sidebar:
            st.markdown("<h3>Filtros</h3>", unsafe_allow_html=True)
            area_options = ["Todos"] + sorted(df['user_area'].unique())
            selected_area = st.selectbox("Área", area_options)

            user_options = ["Todos"] + sorted(df['user_name'].unique())
            selected_user = st.selectbox("Colaborador", user_options)

        # Aplicar filtros
        filtered_df = df.copy()
        if selected_area != "Todos":
            filtered_df = filtered_df[filtered_df['user_area'] == selected_area]

        if selected_user != "Todos":
            filtered_df = filtered_df[filtered_df['user_name'] == selected_user]

        # Exibir quantidade total de certificações pelos filtros
        st.markdown("<h3>Quantidade de Certificações</h3>", unsafe_allow_html=True)
        st.info(f"Total de certificações encontradas: {len(filtered_df)}")

        # Tratar o campo de data para evitar erros de formatação
        def parse_date_safe(date_str):
            try:
                return pd.to_datetime(date_str, format="%Y-%m-%d", errors='coerce')
            except Exception:
                return pd.NaT

        df['certification_date'] = df['certification_date'].apply(parse_date_safe)
        df = df.dropna(subset=['certification_date'])

        # Calcular totais por parceiro (tabela estática)
        total_partner_counts = df['ferramenta_certificacao'].value_counts().sort_values(ascending=False)
        partner_table = total_partner_counts.reset_index()
        partner_table.columns = ["Parceiro", "Total de Certificações"]

        # Adicionar linha final com o total
        total_row = pd.DataFrame({"Parceiro": ["Total"], "Total de Certificações": [total_partner_counts.sum()]})
        partner_table = pd.concat([partner_table, total_row], ignore_index=True)

        # Exibir a tabela antes do gráfico
        st.markdown("<h3>Total de Certificações por Parceiro</h3>", unsafe_allow_html=True)
        st.dataframe(partner_table[['Parceiro', 'Total de Certificações']], use_container_width=True)

        # Gráfico de barras verticais (Total por parceiros)
        st.markdown("<h3>Total de certificações por Parceiros</h3>", unsafe_allow_html=True)

        if not filtered_df.empty:
            partner_counts = filtered_df['ferramenta_certificacao'].value_counts().sort_values(ascending=False)

            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(partner_counts.index, partner_counts.values)

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', ha='center', va='bottom')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            st.pyplot(fig)
        else:
            st.warning("Não há dados para exibir o gráfico.")

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
