"""
Dashboard Operacional (BDR).
KPIs individuais e métricas por canal.
"""
import streamlit as st
import pandas as pd
from charts.kpi_cards import display_kpi_grid
from charts.bars import bar_chart, horizontal_bar_chart
from charts.lines import line_chart
from charts.funnels import funnel_chart
from data.loader import get_descartados_valores_em_real

def render_operational_dashboard(df: pd.DataFrame):
    """
    Renderiza dashboard operacional para BDR com métricas individuais.
    """
    st.title("📈 Dashboard Operacional")
    st.info("💡 **Observação:** Todos os valores de Pipeline e Booking estão em **USD (Dólares Americanos)")
    
    if df.empty:
        st.warning("Nenhum dado disponível para seu acesso.")
        return
    
    bdr_name = df["BDR"].iloc[0] if not df.empty else "Desconhecido"
    st.markdown(f"### Bem-vindo, **{bdr_name}**")
    st.markdown("---")
    
    # === Cálculo de todos os KPIs ===
    # Leads
    total_leads = df['Total Leads'].fillna(0).sum()
    novos_leads = df['Novos Leads'].fillna(0).sum()
    leads_reengajamento = df['Leads Reengajamento'].fillna(0).sum()
    
    # Reuniões
    reuniao_agendada = df['Reuniao Agendada'].fillna(0).sum()
    reuniao_realizada = df['Reuniao Realizada'].fillna(0).sum()
    reuniao_aguardando = df['Reuniao Aguardando'].fillna(0).sum()
    
    # Respostas
    respostas_positivas = df['Total positivas'].fillna(0).sum()
    respostas_negativas = df['Total Negativas'].fillna(0).sum()
    respostas_totais = respostas_positivas + respostas_negativas
    
    # Respostas por canal
    resp_pos_linkedin = df['Resposta Positivo Linkedin'].fillna(0).sum()
    resp_neg_linkedin = df['Resposta Negativa Linkedin'].fillna(0).sum()
    resp_tot_linkedin = resp_pos_linkedin + resp_neg_linkedin
    
    resp_pos_whatsapp = df['Resposta Positivo WhatsApp'].fillna(0).sum()
    resp_neg_whatsapp = df['Resposta Negativa WhatsApp'].fillna(0).sum()
    resp_tot_whatsapp = resp_pos_whatsapp + resp_neg_whatsapp
    
    resp_pos_ligacao = df['Resposta Positivo Ligacao'].fillna(0).sum()
    resp_neg_ligacao = df['Resposta Negativa Ligacao'].fillna(0).sum()
    resp_tot_ligacao = resp_pos_ligacao + resp_neg_ligacao
    
    resp_pos_email = df['Resposta Positivo E-mail'].fillna(0).sum()
    resp_neg_email = df['Resposta Negativa E-mail'].fillna(0).sum()
    resp_tot_email = resp_pos_email + resp_neg_email
    
    # Propostas
    proposta_enviadas = df['Proposta Enviadas'].fillna(0).sum()
    propostas_aceitas = df['Propostas Aceitas'].fillna(0).sum()
    propostas_recusadas = df['Propostas Recusadas'].fillna(0).sum()
    
    # Pipeline e Booking
    pipeline_total = df['Pipeline'].fillna(0).sum()
    booking_total = df['Booking TCV'].fillna(0).sum()
    
    # === KPI BLOCK 1: Leads ===
    st.subheader("📍 KPIs de Leads")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total de Leads", f"{total_leads:,.0f}")
    with col2:
        prop_reengajamento = (leads_reengajamento / total_leads * 100) if total_leads > 0 else 0
        st.metric("% Reengajamento", f"{prop_reengajamento:.1f}%")
    with col3:
        prop_novos = (novos_leads / total_leads * 100) if total_leads > 0 else 0
        st.metric("% Novos Leads", f"{prop_novos:.1f}%")
    
    st.markdown("---")
    
    # === KPI BLOCK 2: Resposta e Abordagem ===
    st.subheader("📞 KPIs de Resposta e Abordagem")
    
    col1, col2 = st.columns(2)
    with col1:
        taxa_resp_pos = (respostas_positivas / respostas_totais * 100) if respostas_totais > 0 else 0
        st.metric("Taxa de Resposta Positiva", f"{taxa_resp_pos:.1f}%")
    with col2:
        taxa_resp_neg = (respostas_negativas / respostas_totais * 100) if respostas_totais > 0 else 0
        st.metric("Taxa de Resposta Negativa", f"{taxa_resp_neg:.1f}%")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        taxa_linkedin = (resp_pos_linkedin / resp_tot_linkedin * 100) if resp_tot_linkedin > 0 else 0
        st.metric("Taxa LinkedIn", f"{taxa_linkedin:.1f}%")
    with col2:
        taxa_whatsapp = (resp_pos_whatsapp / resp_tot_whatsapp * 100) if resp_tot_whatsapp > 0 else 0
        st.metric("Taxa WhatsApp", f"{taxa_whatsapp:.1f}%")
    with col3:
        taxa_ligacao = (resp_pos_ligacao / resp_tot_ligacao * 100) if resp_tot_ligacao > 0 else 0
        st.metric("Taxa Ligação", f"{taxa_ligacao:.1f}%")
    with col4:
        taxa_email = (resp_pos_email / resp_tot_email * 100) if resp_tot_email > 0 else 0
        st.metric("Taxa E-mail", f"{taxa_email:.1f}%")
    
    st.markdown("---")
    
    # === KPI BLOCK 3: Reuniões ===
    st.subheader("🗓️ KPIs de Reuniões")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        taxa_agendamento = (reuniao_agendada / total_leads * 100) if total_leads > 0 else 0
        st.metric("Taxa de Agendamento", f"{taxa_agendamento:.1f}%")
    with col2:
        taxa_comparecimento = (reuniao_realizada / reuniao_agendada * 100) if reuniao_agendada > 0 else 0
        st.metric("Taxa de Comparecimento", f"{taxa_comparecimento:.1f}%")
    with col3:
        taxa_aguardando = (reuniao_aguardando / reuniao_agendada * 100) if reuniao_agendada > 0 else 0
        st.metric("Taxa de Aguardando", f"{taxa_aguardando:.1f}%")
    
    st.markdown("---")
    
    # === KPI BLOCK 4: Propostas ===
    st.subheader("📋 KPIs de Propostas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        taxa_prop_enviadas = (proposta_enviadas / reuniao_realizada * 100) if reuniao_realizada > 0 else 0
        st.metric("Propostas por Reunião", f"{taxa_prop_enviadas:.1f}%")
    with col2:
        taxa_aceite = (propostas_aceitas / proposta_enviadas * 100) if proposta_enviadas > 0 else 0
        st.metric("Taxa de Aceite", f"{taxa_aceite:.1f}%")
    with col3:
        taxa_recusa = (propostas_recusadas / proposta_enviadas * 100) if proposta_enviadas > 0 else 0
        st.metric("Taxa de Recusa", f"{taxa_recusa:.1f}%")
    
    st.markdown("---")
    
    # === KPI BLOCK 5: Pipeline e Valor ===
    st.subheader("💰 KPIs de Pipeline e Valor")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pipeline Total (USD)", f"${pipeline_total:,.2f}")
    with col2:
        pipeline_por_lead = (pipeline_total / total_leads) if total_leads > 0 else 0
        st.metric("Pipeline por Lead (USD)", f"${pipeline_por_lead:,.2f}")
    with col3:
        pipeline_por_reuniao = (pipeline_total / reuniao_realizada) if reuniao_realizada > 0 else 0
        st.metric("Pipeline por Reunião (USD)", f"${pipeline_por_reuniao:,.2f}")
    with col4:
        st.metric("Booking Total (USD)", f"${booking_total:,.2f}")
    st.markdown("---")
    
    # === KPI BLOCK 6: Financeiro ===
    st.subheader("💵 KPIs Financeiros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        booking_por_proposta = (booking_total / propostas_aceitas) if propostas_aceitas > 0 else 0
        st.metric("Booking Médio por Proposta (USD)", f"${booking_por_proposta:,.2f}")
    with col2:
        booking_por_lead = (booking_total / total_leads) if total_leads > 0 else 0
        st.metric("Booking por Lead (USD)", f"${booking_por_lead:,.2f}")
    with col3:
        conversao_funil = (propostas_aceitas / total_leads * 100) if total_leads > 0 else 0
        st.metric("Conversão Final do Funil", f"{conversao_funil:.1f}%")
    
    st.markdown("---")
    
    # === Leads ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Novos Leads", f"{df['Novos Leads'].fillna(0).sum():.0f}")
        st.metric("Leads Reengajamento", f"{df['Leads Reengajamento'].fillna(0).sum():.0f}")
    
    with col2:
        st.metric("Reunião Agendada", f"{df['Reuniao Agendada'].fillna(0).sum():.0f}")
        st.metric("Reunião Aguardando", f"{df['Reuniao Aguardando'].fillna(0).sum():.0f}")
    
    st.markdown("---")
    
    # === Respostas por Canal ===
    st.subheader("Respostas por Canal")
    
    canais_data = []
    canais = {
        "LinkedIn": ("Resposta Positivo Linkedin", "Resposta Negativa Linkedin"),
        "WhatsApp": ("Resposta Positivo WhatsApp", "Resposta Negativa WhatsApp"),
        "Ligação": ("Resposta Positivo Ligacao", "Resposta Negativa Ligacao"),
        "E-mail": ("Resposta Positivo E-mail", "Resposta Negativa E-mail"),
    }
    
    for canal, (pos_col, neg_col) in canais.items():
        canais_data.append({
            "Canal": canal,
            "Positivas": df[pos_col].fillna(0).sum(),
            "Negativas": df[neg_col].fillna(0).sum(),
        })
    
    df_canais = pd.DataFrame(canais_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        bar_chart(df_canais, x="Canal", y="Positivas", title="Respostas Positivas")
    
    with col2:
        bar_chart(df_canais, x="Canal", y="Negativas", title="Respostas Negativas")
    
    st.markdown("---")
    
    # === Funil de Reuniões ===
    st.subheader("Funil de Reuniões")
    reunioes = {
        "Agendadas": df["Reuniao Agendada"].fillna(0).sum(),
        "Aguardando": df["Reuniao Aguardando"].fillna(0).sum(),
        "Realizadas": df["Reuniao Realizada"].fillna(0).sum(),
    }
    stages = list(reunioes.keys())
    values = list(reunioes.values())
    funnel_chart(stages, values, "Progresso de Reuniões")
    
    st.markdown("---")
    
    # === Propostas ===
    st.subheader("Propostas")
    propostas = {
        "Enviadas": df["Proposta Enviadas"].fillna(0).sum(),
        "Aceitas": df["Propostas Aceitas"].fillna(0).sum(),
        "Recusadas": df["Propostas Recusadas"].fillna(0).sum(),
    }
    stages = list(propostas.keys())
    values = list(propostas.values())
    funnel_chart(stages, values, "Funil de Propostas")
    
    st.markdown("---")
    
    # === Tabela de Dados ===
    st.subheader("Seu Histórico")
    # Formatar coluna Ano como inteiro
    df_display = df.copy()
    if "Ano" in df_display.columns:
        df_display["Ano"] = df_display["Ano"].astype(int)
    st.dataframe(df_display, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # === Alerta de Valores em Real Descartados ===
    valores_descartados = get_descartados_valores_em_real()
    if valores_descartados:
        st.warning(f"⚠️ **Aviso:** Foram encontrados {len(valores_descartados)} valor(es) em **Real (R$)** na planilha que foram **descartados** dos cálculos (apenas USD é considerado).")
        with st.expander("📋 Ver valores descartados"):
            for idx, valor in enumerate(valores_descartados, 1):
                st.write(f"{idx}. {valor}")
