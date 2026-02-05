"""
Dashboard Executivo (Admin).
KPIs agregados e visões consolidadas com filtros por BDR.
"""
import streamlit as st
import pandas as pd
from charts.kpi_cards import display_kpi_grid
from charts.bars import bar_chart
from charts.lines import line_chart
from charts.funnels import funnel_chart
from data.loader import get_descartados_valores_em_real
from data.score import compute_bdr_performance_score

def classificar_performance(score: float) -> str:
    if score >= 0.75:
        return "Excelente"
    elif 0.60 <= score < 0.75:
        return "Boa"
    elif 0.45 <= score < 0.60:
        return "Regular"
    else:
        return "Atenção"

def render_executive_dashboard(df: pd.DataFrame):
    """
    Renderiza dashboard executivo com KPIs e visualizações consolidadas.
    Dados já filtrados pela sidebar.
    """
    st.info("💡 **Observação:** Todos os valores de Pipeline e Booking estão em **USD (Dólares Americanos)**")
    st.markdown("---")
    
    # === Score de Performance do BDR ===
    st.subheader("🏆 Score de Performance do BDR")

    try:
        score_df = compute_bdr_performance_score(df)

        # Garantir coluna de semana
        if "Semana 1º contato" in df.columns:
            score_df["Semana"] = df["Semana 1º contato"].dt.strftime("%d/%m/%Y")
        elif "Semana" not in score_df.columns:
            score_df["Semana"] = "—"

        # Padronizar coluna de score
        score_df = score_df.rename(
            columns={"Score de Performance": "Score"}
        )

        # Criar coluna de Performance (faixa)
        score_df["Performance"] = score_df["Score"].apply(classificar_performance)

        # Selecionar e ordenar colunas finais
        score_display = score_df[
            ["Semana", "BDR", "Score", "Performance"]
        ].sort_values(
            by=["Semana", "Score"],
            ascending=[True, False]
        )

        # REMOVER ÍNDICE
        score_display = score_display.reset_index(drop=True)

        score_display["Score"] = score_display["Score"].apply(lambda x: f"{x:.2%}")

        st.dataframe(
            score_display,
            use_container_width=True,
            height=350,
            hide_index=True
        )

    except Exception as e:
        st.error(f"Não foi possível calcular o Score de Performance: {e}")

    # === Cálculo de todos os KPIs ==="
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
    
    # === Visualizações (Responsivas ao Filtro) ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribuição de Leads")
        # Sempre mostra gráfico de barras, mesmo com 1 BDR
        bdrs_unicos = df["BDR"].nunique()
        df_bdrs = df.groupby("BDR")["Total Leads"].sum().reset_index().sort_values("Total Leads", ascending=False)
        bar_chart(df_bdrs, x="BDR", y="Total Leads", title="Leads por BDR")
    
    with col2:
        st.subheader("Reuniões por BDR")
        # Gráfico de reuniões por BDR com status
        df_reunioes = df.groupby("BDR")[["Reuniao Agendada", "Reuniao Aguardando", "Reuniao Realizada"]].sum().reset_index()
        
        # Reformatar para o formato esperado pelo gráfico
        reunioes_data = []
        for _, row in df_reunioes.iterrows():
            reunioes_data.append({"BDR": row["BDR"], "Status": "Agendadas", "Quantidade": row["Reuniao Agendada"]})
            reunioes_data.append({"BDR": row["BDR"], "Status": "Aguardando", "Quantidade": row["Reuniao Aguardando"]})
            reunioes_data.append({"BDR": row["BDR"], "Status": "Realizadas", "Quantidade": row["Reuniao Realizada"]})
        
        df_reunioes_chart = pd.DataFrame(reunioes_data)
        bar_chart(df_reunioes_chart, x="BDR", y="Quantidade", title="Reuniões por BDR", color="Status")
    
    st.markdown("---")
    
    # === Status de Propostas ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Propostas por BDR")
        # Gráfico de propostas por BDR com status
        df_propostas = df.groupby("BDR")[["Proposta Enviadas", "Propostas Aceitas", "Propostas Recusadas"]].sum().reset_index()
        
        # Reformatar para o formato esperado pelo gráfico
        propostas_data = []
        for _, row in df_propostas.iterrows():
            propostas_data.append({"BDR": row["BDR"], "Status": "Enviadas", "Quantidade": row["Proposta Enviadas"]})
            propostas_data.append({"BDR": row["BDR"], "Status": "Aceitas", "Quantidade": row["Propostas Aceitas"]})
            propostas_data.append({"BDR": row["BDR"], "Status": "Recusadas", "Quantidade": row["Propostas Recusadas"]})
        
        df_propostas_chart = pd.DataFrame(propostas_data)
        bar_chart(df_propostas_chart, x="BDR", y="Quantidade", title="Propostas por BDR", color="Status")
    
    with col2:
        st.subheader("Respostas por Canal")
        canais_data = {
            "LinkedIn": {
                "Positivas": df["Resposta Positivo Linkedin"].fillna(0).sum(),
                "Negativas": df["Resposta Negativa Linkedin"].fillna(0).sum(),
            },
            "WhatsApp": {
                "Positivas": df["Resposta Positivo WhatsApp"].fillna(0).sum(),
                "Negativas": df["Resposta Negativa WhatsApp"].fillna(0).sum(),
            },
            "Ligação": {
                "Positivas": df["Resposta Positivo Ligacao"].fillna(0).sum(),
                "Negativas": df["Resposta Negativa Ligacao"].fillna(0).sum(),
            },
            "E-mail": {
                "Positivas": df["Resposta Positivo E-mail"].fillna(0).sum(),
                "Negativas": df["Resposta Negativa E-mail"].fillna(0).sum(),
            },
        }
        
        df_canais = []
        for canal, respostas in canais_data.items():
            for tipo, valor in respostas.items():
                df_canais.append({"Canal": canal, "Tipo": tipo, "Valor": valor})
        
        df_canais = pd.DataFrame(df_canais)
        bar_chart(df_canais, x="Canal", y="Valor", title="Respostas por Canal", color="Tipo")
    
    st.markdown("---")
    
    # === Tabela detalhada ===
    st.subheader("Dados Detalhados")
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

