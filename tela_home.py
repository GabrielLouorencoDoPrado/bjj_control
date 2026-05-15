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

    # --- CONFIGURAÇÕES GERAIS ---
    meses_pt = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
        7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    
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
    # --- MÉTRICAS DO TOPO (BASE DE ATIVOS E FINANCEIRO) ---
    # =========================================================
    qtd_pagantes = 0
    qtd_bolsistas = 0
    qtd_totais = 0
    faturamento_mes = 0.0
    qtd_leads_frios = 0
    qtd_matriculados_geral = 0
    
    if not df_st.empty and not df_att.empty:
        # 1. Pega todo mundo que teve aula no mês atual
        pres_mes = df_att[df_att['Data'].dt.month == hoje.month].copy()
        ids_presentes_mes = pres_mes['Aluno_ID'].unique()
        
        # 2. Pega os matriculados no sistema
        df_matriculados = df_st[df_st['Ativo'] == True].copy()
        qtd_matriculados_geral = len(df_matriculados)
        
        # 3. Dos matriculados, quem REALMENTE veio neste mês?
        df_ativos_mes = df_matriculados[df_matriculados['ID'].isin(ids_presentes_mes)].copy()
        qtd_totais = len(df_ativos_mes)
        
        # 4. Separa Pagantes e Bolsistas DENTRO dos que vieram
        df_bolsistas = df_ativos_mes[df_ativos_mes['Perfil_Financeiro'] == 'Bolsista']
        df_pagantes = df_ativos_mes[df_ativos_mes['Perfil_Financeiro'] != 'Bolsista'].copy()
        
        qtd_bolsistas = len(df_bolsistas)
        qtd_pagantes = len(df_pagantes)
        
        # 5. Calcula o Faturamento APENAS dos Pagantes que vieram no mês
        df_pagantes['V'] = pd.to_numeric(df_pagantes['Valor_Base'], errors='coerce').fillna(0)
        df_pagantes['D'] = pd.to_numeric(df_pagantes['Desconto_Percentual'], errors='coerce').fillna(0)
        faturamento_mes = (df_pagantes['V'] * (1 - df_pagantes['D']/100)).sum()
        
        # --- CÁLCULO DOS LEADS FRIOS ---
        limite_30_dias = hoje - timedelta(days=30)
        ids_matriculados = df_matriculados['ID'].tolist()
        
        df_historico_alunos = df_att.groupby('Aluno_ID').agg(
            Ultima_Aula=('Data', 'max'),
            Total_Aulas=('Data', 'count')
        ).reset_index()
        
        leads_perdidos = df_historico_alunos[
            (~df_historico_alunos['Aluno_ID'].isin(ids_matriculados)) & 
            (df_historico_alunos['Total_Aulas'] <= 2) & 
            (df_historico_alunos['Ultima_Aula'] < limite_30_dias)
        ]
        qtd_leads_frios = len(leads_perdidos)

    # --- EXIBIÇÃO DOS INDICADORES NO TOPO ---
    st.subheader(f"Visão Geral: {meses_pt[hoje.month]}")
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    
    m1.metric("Pagantes (No mês)", qtd_pagantes, help="Matriculados, não-bolsistas, que vieram este mês.")
    m2.metric("Bolsistas (No mês)", qtd_bolsistas, help="Matriculados bolsistas que vieram este mês.")
    m3.metric("Ativos Totais", qtd_totais, help="Pagantes + Bolsistas que frequentaram este mês.")
    m4.metric("Faturamento", f"R$ {faturamento_mes:.2f}", help="Soma das mensalidades APENAS dos pagantes que vieram.")
    m5.metric("Leads Frios", qtd_leads_frios, help="Até 2 aulas experimentais, sumidos há mais de 30 dias.")
    m6.metric("Matriculados (Geral)", qtd_matriculados_geral, help="Total de alunos com cadastro ativo no sistema.")

    st.divider()

    # =========================================================
    # --- MATRÍCULAS E RADAR DE AUSÊNCIA ---
    # =========================================================
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
        periodo_sel = cf1.selectbox("Período de Análise:", ["Últimos 7 dias", "Últimos 15 dias", "Últimos 30 dias", "Todo o período", "Digitar dias manualmente"], index=2) # Index 2 = Últimos 30 dias
        
        dias_calculo = 30
        if periodo_sel == "Digitar dias manualmente":
            dias_calculo = cf1.number_input("Digite a qtd de dias:", min_value=1, value=45, step=1)
            titulo_graficos = f"Análise dos últimos {dias_calculo} dias"
        elif periodo_sel == "Todo o período":
            titulo_graficos = "Análise de Todo o Período"
        else:
            if periodo_sel == "Últimos 7 dias": dias_calculo = 7
            elif periodo_sel == "Últimos 15 dias": dias_calculo = 15
            elif periodo_sel == "Últimos 30 dias": dias_calculo = 30
            titulo_graficos = f"Análise: {periodo_sel}"
            
        data_inicio = hoje - timedelta(days=dias_calculo) if periodo_sel != "Todo o período" else pd.to_datetime("2000-01-01")
        
        cf2.markdown("**Status dos Alunos:**")
        cb1, cb2, cb3, cb4 = cf2.columns(4)
        chk_nor = cb1.checkbox("Normal", value=True)
        chk_rep = cb2.checkbox("Reposição", value=True)
        chk_exp = cb3.checkbox("Experimental", value=True)
        chk_vis = cb4.checkbox("Visita", value=True)
        
        status_sel = []
        if chk_nor: status_sel.append("Normal")
        if chk_rep: status_sel.append("Reposição")
        if chk_exp: status_sel.append("Experimental")
        if chk_vis: status_sel.append("Visita")

        df_bi = df_att.copy()
        if not df_bi.empty:
            df_bi = df_bi[(df_bi['Data'] >= data_inicio) & (df_bi['Status_Aula'].isin(status_sel))]
        
        if not df_bi.empty:
            csv = df_bi.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Dados Filtrados (CSV)", data=csv, file_name="relatorio_tatame.csv", mime="text/csv")

    tab1, tab2, tab3 = st.tabs(["🔥 Mapa de Calor", "📈 Volume Faded", "👥 Proporção de Turmas"])

    with tab1:
        if not df_bi.empty:
            mapa_dias = {0: '1-Seg', 1: '2-Ter', 2: '3-Qua', 3: '4-Qui', 4: '5-Sex', 5: '6-Sáb', 6: '7-Dom'}
            df_bi['Dia_Semana'] = df_bi['Data'].dt.dayofweek.map(mapa_dias)
            df_bi['Data_Exata'] = df_bi['Data'].dt.date
            df_conta_dia = df_bi.groupby(['Turma', 'Dia_Semana', 'Data_Exata']).size().reset_index(name='Qtd')
            df_media_calor = df_conta_dia.groupby(['Turma', 'Dia_Semana'])['Qtd'].mean().reset_index(name='Média')
            
            # Arredondando para 1 casa decimal (Correção 1)
            df_media_calor['Média'] = df_media_calor['Média'].round(1) 
            
            fig_h = px.scatter(df_media_calor, x='Dia_Semana', y='Turma', size='Média', color='Média', 
                               color_continuous_scale='Reds', size_max=28, text='Média', 
                               category_orders={"Turma": ordem_turmas, "Dia_Semana": ordem_dias},
                               title=f"Média de Alunos por Dia da Semana ({titulo_graficos})")
            fig_h.update_layout(xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,b=0,t=40))
            st.plotly_chart(fig_h, use_container_width=True)

    with tab2:
        if not df_bi.empty:
            df_v = df_bi.groupby(df_bi['Data'].dt.date).size().reset_index(name='Presenças')
            df_v['Data_Texto'] = pd.to_datetime(df_v['Data']).dt.strftime('%d/%m')
            
            # Forçando a exibição do texto sempre (Correção 2)
            fig_v = px.line(df_v, x='Data_Texto', y='Presenças', line_shape='spline', text='Presenças',
                            title=f"Evolução Diária de Presenças ({titulo_graficos})")
            
            # Ajustando a posição do texto para não cortar e flutuar acima da linha
            max_y = df_v['Presenças'].max()
            fig_v.update_traces(fill='tozeroy', fillcolor='rgba(39, 174, 96, 0.15)', line_color='#27AE60', 
                                line_width=3, textposition='top center')
            fig_v.update_layout(margin=dict(l=20, r=40, t=40, b=20), xaxis_title=None, yaxis_title=None, 
                                xaxis_type='category', yaxis=dict(range=[0, max_y * 1.15])) # Espaço extra pro rótulo
            st.plotly_chart(fig_v, use_container_width=True)

    with tab3:
        if not df_bi.empty:
            cp1, cp2 = st.columns(2)
            with cp1:
                df_pizza = df_bi.groupby('Turma', observed=True)['Aluno_ID'].nunique().reset_index(name='Total')
                fig_p = px.pie(df_pizza, names='Turma', values='Total', hole=0.4, 
                               category_orders={"Turma": ordem_turmas}, color_discrete_sequence=px.colors.qualitative.Pastel,
                               title=f"Distribuição de Alunos Ativos ({titulo_graficos})")
                st.plotly_chart(fig_p, use_container_width=True)
            with cp2:
                df_barras = df_bi.groupby(['Turma', 'Status_Aula'], observed=True)['Aluno_ID'].nunique().reset_index(name='Total')
                fig_b = px.bar(df_barras, x='Turma', y='Total', color='Status_Aula', barmode='stack', 
                               category_orders={"Turma": ordem_turmas}, color_discrete_map=cores_status,
                               title=f"Perfil de Frequência por Turma ({titulo_graficos})")
                st.plotly_chart(fig_b, use_container_width=True)

    st.divider()
    st.subheader(f"🎂 Aniversariantes de {meses_pt[hoje.month]}")
    if not df_st.empty:
        anivs = df_st[df_st['Data_Nascimento'].dt.month == hoje.month]
        if not anivs.empty:
            cols = st.columns(4)
            for i, (_, r) in enumerate(anivs.reset_index().iterrows()):
                cols[i % 4].success(f"🎈 **{r['Nome']}**\nDia {r['Data_Nascimento'].day:02d}")
        else: st.info("Nenhum aniversariante este mês.")