import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from database import get_students, get_attendance

def render():
    st.title("🥋 Dashboard de Gestão Estratégica")
    
    df_st = get_students()
    df_att = get_attendance()
    hoje = datetime.now()

    # --- CONFIGURAÇÕES GERAIS E PALETA DE CORES ---
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
    # Ordem das turmas (Usado para orientar o gráfico, sem destruir dados)
    ordem_turmas = ['Jardim I e II', 'EF I', 'EF II', 'EM']
    ordem_dias = ['1-Seg', '2-Ter', '3-Qua', '4-Qui', '5-Sex', '6-Sáb', '7-Dom']
    
    cores_status = {
        'Normal': '#2980B9',        
        'Reposição': '#5DADE2',     
        'Experimental': '#E67E22',  
        'Visita': '#F1C40F'         
    }

    # --- TRATAMENTO DE DADOS ---
    if not df_att.empty:
        df_att['Data'] = pd.to_datetime(df_att['Data'])
        df_att['Turma'] = df_att['Turma'].replace('Jardim', 'Jardim I e II')
        
    if not df_st.empty:
        df_st['Data_Nascimento'] = pd.to_datetime(df_st['Data_Nascimento'], errors='coerce')
        df_st['Turma'] = df_st['Turma'].replace('Jardim', 'Jardim I e II')

    # =========================================================
    # --- MÉTRICAS DO TOPO (REGRA DE NEGÓCIO RIGOROSA) ---
    # =========================================================
    faturamento_real = 0.0
    ids_ativos = []
    leads_unicos_validos = 0
    
    if not df_att.empty and not df_st.empty:
        # 1. ALUNOS ATIVOS: Pelo menos 2 aulas oficiais no mês corrente
        pres_mes = df_att[df_att['Data'].dt.month == hoje.month].copy()
        df_oficiais = pres_mes[pres_mes['Status_Aula'].isin(['Normal', 'Reposição'])]
        contagem_aulas = df_oficiais.groupby('Aluno_ID').size()
        ids_ativos = contagem_aulas[contagem_aulas >= 2].index.tolist()
        
        # 2. FATURAMENTO EFETIVO: Calculado apenas sobre os alunos ativos
        df_fin = df_st[df_st['ID'].isin(ids_ativos)].copy()
        df_fin['V'] = pd.to_numeric(df_fin['Valor_Base'], errors='coerce').fillna(0)
        df_fin['D'] = pd.to_numeric(df_fin['Desconto_Percentual'], errors='coerce').fillna(0)
        faturamento_real = (df_fin['V'] * (1 - df_fin['D']/100)).sum()
        
        # 3. LEADS VIVOS: Únicos e que treinaram nos últimos 15 dias
        limite_15_dias = hoje - timedelta(days=15)
        df_todos_leads = df_att[df_att['Status_Aula'].isin(['Experimental', 'Visita'])].copy()
        
        if not df_todos_leads.empty:
            # Encontra a última data em que cada lead apareceu
            ultima_visita_lead = df_todos_leads.groupby('Aluno_ID')['Data'].max().reset_index()
            # Filtra quem ainda está dentro da janela de 15 dias
            leads_recentes = ultima_visita_lead[ultima_visita_lead['Data'] >= limite_15_dias]['Aluno_ID'].tolist()
            # Remove qualquer lead que já tenha se tornado aluno ativo
            ids_leads_finais = [lid for lid in leads_recentes if lid not in ids_ativos]
            leads_unicos_validos = len(ids_leads_finais)

    st.subheader(f"Desempenho: {meses_pt[hoje.month]}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Alunos Ativos (2+ Aulas)", len(ids_ativos))
    m2.metric("Faturamento Efetivo", f"R$ {faturamento_real:.2f}")
    m3.metric("Leads Quentes (15 dias)", leads_unicos_validos)
    m4.metric("Total Cadastros", len(df_st[df_st['Ativo'] == True]) if not df_st.empty else 0)

    st.divider()

    # --- MATRÍCULAS E RADAR DE AUSÊNCIA ---
    c_mat, c_rad = st.columns([1, 1])

    with c_mat:
        st.subheader("🎯 Prontos para Matrícula")
        if not df_att.empty:
            df_exp = df_att[df_att['Status_Aula'].isin(['Experimental', 'Visita'])].groupby('Nome').size().reset_index(name='E')
            df_nor = df_att[~df_att['Status_Aula'].isin(['Experimental', 'Visita'])].groupby('Nome').size().reset_index(name='N')
            df_merge = pd.merge(df_exp, df_nor, on='Nome', how='left').fillna(0)
            prontos = df_merge[(df_merge['E'] >= 3) & (df_merge['N'] == 0)]
            if not prontos.empty:
                for _, p in prontos.iterrows():
                    st.warning(f"🔥 **{p['Nome']}** ({int(p['E'])} aulas) - Fechar Matrícula!")
            else:
                st.info("Nenhum lead com 3+ aulas pendente.")

    with c_rad:
        st.subheader("⚠️ Radar de Ausência")
        r1, r2 = st.columns(2)
        data_ref = r1.date_input("Parou de vir antes de:", hoje - timedelta(days=7))
        tipo_aluno = r2.selectbox("Filtro:", ["Todos", "Matriculados", "Experimentais"], key="rad_home")

        if not df_st.empty and not df_att.empty:
            df_ult = df_att.groupby('Aluno_ID')['Data'].max().reset_index()
            df_radar = pd.merge(df_st[df_st['Ativo']==True], df_ult, left_on='ID', right_on='Aluno_ID', how='left')
            dt_c = pd.to_datetime(data_ref)
            
            df_lista = df_radar[(df_radar['Data'] < dt_c) | (df_radar['Data'].isnull())].copy()
            id_oficiais = df_att[df_att['Status_Aula'].isin(['Normal', 'Reposição'])]['Aluno_ID'].unique()
            
            if tipo_aluno == "Matriculados": df_lista = df_lista[df_lista['ID'].isin(id_oficiais)]
            elif tipo_aluno == "Experimentais": df_lista = df_lista[~df_lista['ID'].isin(id_oficiais)]

            with st.container(height=180):
                for _, al in df_lista.sort_values('Data', ascending=True).iterrows():
                    dt_txt = al['Data'].strftime('%d/%m') if pd.notna(al['Data']) else "Sem registro"
                    st.write(f"{'🥋' if al['ID'] in id_oficiais else '🚶‍♂️'} **{al['Nome']}** ({al['Turma']}) - Último: {dt_txt}")

    st.divider()

    # =========================================================
    # --- PAINEL DE BI: INTELIGÊNCIA DE TATAME ---
    # =========================================================
    st.subheader("📊 Inteligência de Tatame")
    
    with st.container(border=True):
        st.markdown("#### 🎛️ Filtros Globais do Painel")
        cf1, cf2 = st.columns([1, 2])
        
        periodo_sel = cf1.selectbox(
            "Período de Análise:", 
            ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Todo o período", "Digitar dias manualmente"],
            index=3 
        )
        
        dias_calculo = 30
        if periodo_sel == "Digitar dias manualmente":
            dias_calculo = cf1.number_input("Digite a qtd de dias:", min_value=1, value=45, step=1)
        elif periodo_sel == "Últimos 7 dias": dias_calculo = 7
        elif periodo_sel == "Últimos 15 dias": dias_calculo = 15
        elif periodo_sel == "Últimos 30 dias": dias_calculo = 30
        
        data_inicio = hoje - timedelta(days=dias_calculo) if periodo_sel != "Todo o período" else pd.to_datetime("2000-01-01")
        
        cf2.markdown("**Status dos Alunos (Combine como quiser):**")
        cb1, cb2, cb3, cb4 = cf2.columns(4)
        chk_nor = cb1.checkbox("Normal", value=True)
        chk_rep = cb2.checkbox("Reposição", value=True)
        chk_exp = cb3.checkbox("Experimental", value=True)
        chk_vis = cb4.checkbox("Visita", value=True)
        
        status_selecionados = []
        if chk_nor: status_selecionados.append("Normal")
        if chk_rep: status_selecionados.append("Reposição")
        if chk_exp: status_selecionados.append("Experimental")
        if chk_vis: status_selecionados.append("Visita")

        # Aplicação dos Filtros Master
        df_bi = df_att.copy()
        if not df_bi.empty:
            df_bi = df_bi[(df_bi['Data'] >= data_inicio) & (df_bi['Status_Aula'].isin(status_selecionados))]
        
        txt_data = "todo o histórico" if periodo_sel == "Todo o período" else f"o período de **{data_inicio.strftime('%d/%m/%Y')}** até hoje"
        
        if df_bi.empty:
            st.warning(f"⚠️ Atenção: Não há presenças registradas para os filtros selecionados ({txt_data}).")
        else:
            st.success(f"🔍 Mostrando **{len(df_bi)} presenças** correspondentes a {txt_data}.")
            csv = df_bi.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Dados Filtrados (CSV)", data=csv, file_name="relatorio_tatame.csv", mime="text/csv")

    # =========================================================
    # --- PLOTAGEM DOS GRÁFICOS ---
    # =========================================================
    tab1, tab2, tab3 = st.tabs(["🔥 Mapa de Calor", "📈 Volume Faded", "👥 Proporção de Turmas"])

    with tab1:
        if not df_bi.empty:
            mapa_dias = {0: '1-Seg', 1: '2-Ter', 2: '3-Qua', 3: '4-Qui', 4: '5-Sex', 5: '6-Sáb', 6: '7-Dom'}
            df_bi['Dia_Semana'] = df_bi['Data'].dt.dayofweek.map(mapa_dias)
            df_bi['Data_Exata'] = df_bi['Data'].dt.date
            
            df_conta_dia = df_bi.groupby(['Turma', 'Dia_Semana', 'Data_Exata']).size().reset_index(name='Qtd')
            df_media_calor = df_conta_dia.groupby(['Turma', 'Dia_Semana'])['Qtd'].mean().reset_index(name='Média')
            df_media_calor['Média'] = df_media_calor['Média'].round(1)
            
            fig_h = px.scatter(df_media_calor, x='Dia_Semana', y='Turma', size='Média', color='Média',
                               color_continuous_scale='Reds', size_max=28, text='Média',
                               category_orders={"Turma": ordem_turmas, "Dia_Semana": ordem_dias})
            
            fig_h.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,b=0,t=10))
            st.plotly_chart(fig_h, use_container_width=True)

    with tab2:
        if not df_bi.empty:
            df_v = df_bi.groupby(df_bi['Data'].dt.date).size().reset_index(name='Presenças')
            df_v['Data_Texto'] = pd.to_datetime(df_v['Data']).dt.strftime('%d/%m')
            
            usar_texto = 'Presenças' if len(df_v) <= 20 else None
            
            fig_v = px.line(df_v, x='Data_Texto', y='Presenças', line_shape='spline', text=usar_texto)
            fig_v.update_traces(fill='tozeroy', fillcolor='rgba(39, 174, 96, 0.15)', line_color='#27AE60', line_width=3, cliponaxis=False)
            
            if usar_texto:
                fig_v.update_traces(textposition='top center')

            fig_v.update_layout(
                margin=dict(l=20, r=40, t=40, b=20),
                xaxis_title=None, yaxis_title=None,
                xaxis_type='category', 
                yaxis=dict(showgrid=False, zeroline=False), 
                xaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_v, use_container_width=True)

    with tab3:
        if not df_bi.empty:
            cp1, cp2 = st.columns(2)
            with cp1:
                st.markdown("**Alunos Únicos por Turma (Pizza)**")
                df_pizza = df_bi.groupby('Turma', observed=True)['Aluno_ID'].nunique().reset_index(name='Total')
                df_pizza = df_pizza[df_pizza['Total'] > 0]
                
                fig_p = px.pie(df_pizza, names='Turma', values='Total', hole=0.4,
                               category_orders={"Turma": ordem_turmas},
                               color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_p, use_container_width=True)
            
            with cp2:
                st.markdown("**Alunos Únicos por Status (Colunas)**")
                df_barras = df_bi.groupby(['Turma', 'Status_Aula'], observed=True)['Aluno_ID'].nunique().reset_index(name='Total')
                df_barras = df_barras[df_barras['Total'] > 0]
                
                fig_b = px.bar(df_barras, x='Turma', y='Total', color='Status_Aula', barmode='stack',
                               category_orders={"Turma": ordem_turmas},
                               color_discrete_map=cores_status)
                fig_b.update_layout(xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_b, use_container_width=True)

    # --- ANIVERSARIANTES ---
    st.divider()
    st.subheader(f"🎂 Aniversariantes de {meses_pt[hoje.month]}")
    if not df_st.empty:
        anivs = df_st[df_st['Data_Nascimento'].dt.month == hoje.month]
        if not anivs.empty:
            cols = st.columns(4)
            for i, (_, r) in enumerate(anivs.reset_index().iterrows()):
                cols[i % 4].success(f"🎈 **{r['Nome']}**\nDia {r['Data_Nascimento'].day:02d}")
        else:
            st.info("Nenhum aniversariante registrado neste mês.")