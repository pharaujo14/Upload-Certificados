import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

# Carregar logos
logo_astronauta = Image.open("logo.png")
logo_century = Image.open("logo_site.png")

def pagina_relatorios(db):

    # Header
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image(logo_astronauta, width=150)
    with col2:
        st.markdown("<h1 style='text-align: center; color: black;'>📊 Dashboard de Certificações</h1>", unsafe_allow_html=True)
    with col3:
        st.image(logo_century, width=150)

    try:
        data = list(db.find())
        df = pd.DataFrame(data)

        # ========================
        # === Prepara Dados Base ==
        # ========================

        df['certification_date'] = pd.to_datetime(df['certification_date'], errors='coerce')
        df = df.dropna(subset=['certification_date'])

        users_collection = db["users"]
        usuarios_ativos = list(users_collection.find({"ativo": True}))
        total_usuarios = users_collection.count_documents({})
        total_ativos = len(usuarios_ativos)
        perc_ativos = (total_ativos / total_usuarios * 100) if total_usuarios > 0 else 0

        nomes_ativos = [u.get("nome") for u in usuarios_ativos]

        # ========================
        # ========= KPIs ==========
        # ========================

        st.markdown("### 📌 Indicadores Gerais")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Certificações", len(df))
        col2.metric("Certificações por Área", df['user_area'].nunique())
        col3.metric("% Usuários Ativos", f"{perc_ativos:.0f}%")

        st.markdown("---")

        # ========================
        # ======== FILTROS ========
        # ========================

        with st.sidebar:
            st.markdown("### 🎛️ Filtros")

            area_options = ["Todos"] + sorted(df['user_area'].unique())
            selected_area = st.selectbox("Área", area_options)

            user_options = ["Todos", "Apenas Ativos"] + sorted(df['user_name'].unique())
            selected_user = st.selectbox("Colaborador", user_options)

            fabricante_options = ["Todos"] + sorted(df['ferramenta_certificacao'].unique())
            selected_fabricante = st.selectbox("Fabricante", fabricante_options)

        filtered_df = df.copy()

        if selected_area != "Todos":
            filtered_df = filtered_df[filtered_df['user_area'] == selected_area]

        if selected_user == "Apenas Ativos":
            filtered_df = filtered_df[filtered_df['user_name'].isin(nomes_ativos)]
        elif selected_user != "Todos":
            filtered_df = filtered_df[filtered_df['user_name'] == selected_user]

        if selected_fabricante != "Todos":
            filtered_df = filtered_df[filtered_df['ferramenta_certificacao'] == selected_fabricante]

        # ========================
        # ======= RELATÓRIOS ======
        # ========================

        st.markdown(f"<h4 style='text-align:center;'>Total de Certificações Filtradas: {len(filtered_df)}</h4>", unsafe_allow_html=True)

        # ---------------------
        # Relatório 1 - Por Parceiro
        # ---------------------
        st.markdown("### ✅ Certificações por Parceiro")

        partner_table = df['ferramenta_certificacao'].value_counts().reset_index()
        partner_table.columns = ["Parceiro", "Total de Certificações"]
        partner_table = pd.concat([partner_table, pd.DataFrame({"Parceiro": ["Total"], "Total de Certificações": [partner_table['Total de Certificações'].sum()]})], ignore_index=True)
        
        # Exibe sem índice
        st.dataframe(partner_table.set_index("Parceiro"), use_container_width=True)

        if not filtered_df.empty:
            st.markdown("#### Gráfico")
            partner_counts = filtered_df['ferramenta_certificacao'].value_counts()
            fig, ax = plt.subplots(figsize=(8, 4))
            bars = ax.bar(partner_counts.index, partner_counts.values)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}', ha='center', va='bottom')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Sem dados para gráfico.")

        # ---------------------
        # Relatório 2 - Por Certificação
        # ---------------------
        st.markdown("### ✅ Certificações por Ferramenta")

        certification_table = (
            filtered_df.groupby(['ferramenta_certificacao', 'certification_name'])
            .size()
            .reset_index(name='Quantidade')
            .rename(columns={"ferramenta_certificacao": "Ferramenta", "certification_name": "Certificação"})
        )

        certification_table = pd.concat([certification_table, pd.DataFrame({"Ferramenta": ["Total"], "Certificação": [""], "Quantidade": [certification_table["Quantidade"].sum()]})], ignore_index=True)

        st.dataframe(certification_table.set_index("Ferramenta"), use_container_width=True)

        # ---------------------
        # Relatório 3 - Por Funcionário
        # ---------------------
        st.markdown("### ✅ Certificações por Funcionário")

        certification_table = (
            filtered_df[['user_name', 'ferramenta_certificacao', 'certification_name']]
            .drop_duplicates()
            .sort_values(by=['user_name', 'ferramenta_certificacao', 'certification_name'])
            .rename(columns={"user_name": "Funcionário", "ferramenta_certificacao": "Ferramenta", "certification_name": "Certificação"})
        )

        total_certifications = len(certification_table)
        certification_table = pd.concat([certification_table, pd.DataFrame({"Funcionário": ["Total"], "Ferramenta": [""], "Certificação": [""]})], ignore_index=True)

        st.dataframe(certification_table.set_index("Funcionário"), use_container_width=True)

        st.markdown(f"<h5 style='text-align:right;'>Total geral de certificações únicas: {total_certifications}</h5>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")