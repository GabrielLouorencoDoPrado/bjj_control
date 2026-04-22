import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import get_students, get_attendance
from gerador_pdf import criar_relatorio_escola # Importando a nova função do PDF

def render():
    st.header("📈 Relatório Financeiro e Evolução")
    df_st = get_students()
    df_att = get_attendance()
    
    if df_att.empty:
        st.info("Sem dados de presença registrados para gerar relatórios.")
        return

    df_att_valido = df_att.dropna(subset=['Data']).copy()
    if df_att_valido.empty:
        st.info("Sem datas válidas registradas.")
        return

    # --- CRIANDO AS DUAS ABAS ---
    tab_graficos, tab_escola = st.tabs(["📊 Visão Geral e Gráficos", "🏫 Exportar para a Escola (PDF)"])

    # ==========================================
    # ABA 1: VISÃO GERAL
    # ==========================================
    with tab_graficos:
        meses_abrev = {
            '01': 'jan', '02': 'fev', '03': 'mar', '04': 'abr', 
            '05': 'mai', '06': 'jun', '07': 'jul', '08': 'ago', 
            '09': 'set', '10': 'out', '11': 'nov', '12': 'dez'
        }
        
        df_att_valido['Chave_Periodo'] = df_att_valido['Data'].dt.strftime('%Y-%m')
        
        def formatar_periodo(chave):
            ano, mes = chave.split('-')
            return f"{meses_abrev[mes]}/{ano[-2:]}"

        periodos_disponiveis = sorted(df_att_valido['Chave_Periodo'].unique())
        
        periodos_selecionados = st.multiselect(
            "📅 Selecione os Períodos para Análise",
            options=periodos_disponiveis,
            default=periodos_disponiveis,
            format_func=formatar_periodo
        )
        
        if not periodos_selecionados:
            st.warning("Selecione pelo menos um período na caixa acima.")
        else:
            df_st['Valor_Base'] = pd.to_numeric(df_st['Valor_Base'], errors='coerce').fillna(0)
            df_st['Desconto_Percentual'] = pd.to_numeric(df_st['Desconto_Percentual'], errors='coerce').fillna(0)
            
            dados_grafico = []
            todos_pagantes_ids = set()
            todos_leads_ids = set()

            for periodo in sorted(periodos_selecionados):
                pres_no_mes = df_att_valido[df_att_valido['Chave_Periodo'] == periodo]
                
                # Considera alunos normais ou em reposição como pagantes
                ids_pagantes_mes = pres_no_mes[pres_no_mes['Status_Aula'].isin(["Normal", "Reposição"])]['Aluno_ID'].unique()
                todos_pagantes_ids.update(ids_pagantes_mes)
                
                cobranca_mes = df_st[df_st['ID'].isin(ids_pagantes_mes)].copy()
                
                if not cobranca_mes.empty:
                    cobranca_mes['Valor_A_Pagar'] = cobranca_mes['Valor_Base'] * (1 - (cobranca_mes['Desconto_Percentual'] / 100))
                    cobranca_mes.loc[cobranca_mes['Perfil_Financeiro'] == 'Bolsista', 'Valor_A_Pagar'] = 0.0
                    faturamento_mes = cobranca_mes['Valor_A_Pagar'].sum()
                else:
                    faturamento_mes = 0.0
                    
                dados_grafico.append({
                    'Período': formatar_periodo(periodo), 
                    'Faturamento Previsto (R$)': faturamento_mes
                })
                
                # Coleta os leads (visitas/experimentais)
                ids_leads_mes = pres_no_mes[pres_no_mes['Status_Aula'].isin(["Experimental", "Visita"])]['Aluno_ID'].unique()
                todos_leads_ids.update(ids_leads_mes)

            df_grafico = pd.DataFrame(dados_grafico)
            faturamento_total_periodo = df_grafico['Faturamento Previsto (R$)'].sum()
            
            st.metric("Faturamento Acumulado (Períodos Selecionados)", f"R$ {faturamento_total_periodo:.2f}")
            
            # --- PLOTAGEM DO GRÁFICO ---
            if len(df_grafico) > 0:
                fig = px.line(
                    df_grafico, x='Período', y='Faturamento Previsto (R$)', text='Faturamento Previsto (R$)', 
                    markers=True, title="Evolução do Faturamento"
                )
                
                fig.update_traces(
                    textposition="top center", texttemplate="R$ %{text:.2f}", line_color='#2ECC71',               
                    fill='tozeroy', fillcolor='rgba(46, 204, 113, 0.2)', cliponaxis=False
                )
                
                max_y = df_grafico['Faturamento Previsto (R$)'].max()
                limite_superior = max_y * 1.2 if max_y > 0 else 100
                
                fig.update_layout(margin=dict(r=50, t=50))
                fig.update_yaxes(rangemode="tozero", range=[0, limite_superior])
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # --- TABELAS DE DETALHES ---
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Lista de Alunos Pagantes (Período)")
                cobranca_geral = df_st[df_st['ID'].isin(todos_pagantes_ids)].copy()
                
                if not cobranca_geral.empty:
                    cobranca_geral['Valor_Mensal'] = cobranca_geral['Valor_Base'] * (1 - (cobranca_geral['Desconto_Percentual'] / 100))
                    cobranca_geral.loc[cobranca_geral['Perfil_Financeiro'] == 'Bolsista', 'Valor_Mensal'] = 0.0
                    st.dataframe(cobranca_geral[['Nome', 'Turma', 'Perfil_Financeiro', 'Valor_Mensal']], hide_index=True, use_container_width=True)
                    
                    csv = cobranca_geral.to_csv(index=False).encode('utf-8')
                    st.download_button("📄 Baixar Lista (CSV)", data=csv, file_name='financeiro_jiujitsu.csv', mime='text/csv')
                else:
                    st.info("Nenhuma mensalidade gerada.")

            with col2:
                st.subheader("Leads (Experimentais/Visitas)")
                leads_geral = df_st[df_st['ID'].isin(todos_leads_ids)]
                leads_puros = leads_geral[~leads_geral['ID'].isin(todos_pagantes_ids)]
                
                if not leads_puros.empty:
                    st.metric("Total de Prospectos", len(leads_puros))
                    
                    for _, lead in leads_puros.iterrows():
                        tel = str(lead.get('Telefone', ''))
                        msg = f"Olá {lead['Nome']}, vi que você treinou com a gente! O que achou da aula?"
                        
                        c_nome, c_link = st.columns([3, 1])
                        c_nome.write(f"👤 {lead['Nome']} ({lead['Turma']})")
                        if tel and tel.strip() != "" and tel.lower() != "nan":
                            link_wa = f"https://wa.me/55{tel}?text={msg.replace(' ', '%20')}"
                            c_link.markdown(f"[📲 Whats]({link_wa})")
                        else:
                            c_link.write("*(Sem tel)*")
                else:
                    st.metric("Total de Prospectos", 0)
                    st.info("Nenhum lead novo neste período.")

    # ==========================================
    # ABA 2: GERAR PDF PARA A ESCOLA
    # ==========================================
    with tab_escola:
        st.subheader("📑 Gerar Relatório de Faturamento Escolar")
        st.markdown("Gera um PDF detalhado apenas com alunos que atingiram a meta de **2 ou mais aulas oficiais** no mês.")
        
        # Pega a lista de meses/anos únicos que já tiveram alguma aula registrada
        df_att_valido['Mes_Ano'] = df_att_valido['Data'].dt.strftime('%m/%Y')
        opcoes_meses = sorted(df_att_valido['Mes_Ano'].unique(), reverse=True)
        
        if opcoes_meses:
            mes_selecionado = st.selectbox("Selecione o mês de fechamento para enviar à escola:", opcoes_meses)
            
            if st.button("⚙️ Processar Relatório PDF", type="primary"):
                mes_str, ano_str = mes_selecionado.split('/')
                
                with st.spinner("Analisando presenças e desenhando o PDF..."):
                    # --- LIMPEZA DE EMOJIS PARA O PDF NÃO QUEBRAR ---
                    df_para_pdf = df_att_valido.copy()
                    
                    # Converte todas as colunas de texto removendo caracteres que o FPDF não suporta (como emojis)
                    for col in df_para_pdf.select_dtypes(include=['object']):
                        df_para_pdf[col] = df_para_pdf[col].apply(
                            lambda x: str(x).encode('latin-1', 'ignore').decode('latin-1') if pd.notna(x) else x
                        )

                    # Chama a função do arquivo gerador_pdf.py com os dados limpos
                    pdf_bytes = criar_relatorio_escola(df_para_pdf, int(mes_str), int(ano_str))
                
                if pdf_bytes:
                    st.success("✅ Relatório gerado com sucesso!")
                    st.download_button(
                        label="⬇️ Baixar Arquivo PDF para a Escola",
                        data=pdf_bytes,
                        file_name=f"Relatorio_BJJ_BomSucesso_{mes_selecionado.replace('/', '_')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.warning(f"Atenção: Nenhum aluno cadastrado atingiu a regra mínima de 2 aulas oficiais no mês de {mes_selecionado}.")
        else:
            st.info("Nenhuma presença registrada no banco de dados ainda.")