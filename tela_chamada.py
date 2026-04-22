import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_students, get_attendance, save_attendance

def render():
    st.header("📋 Chamada e Frequência")
    st.markdown("Registre a presença da turma ou edite lançamentos anteriores.")
    
    # Criando as duas abas
    tab_chamada, tab_edicao = st.tabs(["✅ Fazer Chamada", "✏️ Editar / Apagar Presenças"])

    # ==========================================
    # ABA 1: FAZER CHAMADA (COM SISTEMA DE ALERTAS)
    # ==========================================
    with tab_chamada:
        col_data, col_vazia = st.columns([1, 3])
        with col_data:
            data_aula = st.date_input("📅 Data do Treino", datetime.now(), key="data_chamada_massa")
        
        df_st = get_students()
        
        if df_st.empty:
            st.warning("Nenhum aluno cadastrado ativo. Vá em 'Gestão de Alunos' primeiro.")
            return

        st.divider()
        st.subheader("Fazer Chamada")
        
        df_chamada = df_st[['ID', 'Nome', 'Turma']].copy()
        df_chamada['Presente?'] = False
        df_chamada['Status da Aula'] = 'Normal'
        df_chamada['Alerta'] = '🟢 Normal'
        df_chamada['Observação'] = ''
        
        df_editado = st.data_editor(
            df_chamada,
            column_order=["Nome", "Turma", "Presente?", "Status da Aula", "Alerta", "Observação"],
            column_config={
                "Nome": st.column_config.TextColumn("👤 Nome do Aluno", disabled=True),
                "Turma": st.column_config.TextColumn("🥋 Turma", disabled=True),
                "Presente?": st.column_config.CheckboxColumn("✅ Presente?", default=False),
                "Status da Aula": st.column_config.SelectboxColumn(
                    "📌 Status", 
                    options=["Normal", "Experimental", "Visita", "Reposição"]
                ),
                "Alerta": st.column_config.SelectboxColumn(
                    "⚠️ Comportamento", 
                    options=["🟢 Normal", "🟡 Atenção", "🔴 Grave"]
                ),
                "Observação": st.column_config.TextColumn(
                    "📝 Ocorrência/Obs", 
                    help="Descreva aqui se houve alguma ocorrência"
                )
            },
            hide_index=True,
            use_container_width=True,
            key="editor_chamada"
        )
        
        # --- NOVO BLOCO: REGISTRO DE TÉCNICAS ---
        st.subheader("Conteúdo do Treino")
        tecnicas_dia = st.text_input(
            "🥋 Técnicas Ensinadas Hoje", 
            placeholder="Ex: Armlock da guarda fechada, Passagem toreando...",
            help="O que for digitado aqui será salvo no histórico de todos os alunos presentes."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("💾 Salvar Presenças e Ocorrências", type="primary", use_container_width=True):
            presentes = df_editado[df_editado['Presente?'] == True]
            
            if presentes.empty:
                st.warning("Nenhum aluno foi marcado como presente. Marque a caixinha primeiro.")
            else:
                df_att = get_attendance()
                novas_presencas = []
                
                # Prepara o cabeçalho do WhatsApp
                texto_whats = f"*RELATÓRIO DE TREINO - {data_aula.strftime('%d/%m/%Y')}*\n"
                if tecnicas_dia.strip():
                    texto_whats += f"🥋 *Técnicas:* {tecnicas_dia.strip()}\n"
                texto_whats += "\n"
                
                tem_ocorrencia = False
                
                for _, row in presentes.iterrows():
                    novas_presencas.append({
                        "Data": data_aula,
                        "Aluno_ID": row['ID'],
                        "Nome": row['Nome'],
                        "Turma": row['Turma'],
                        "Status_Aula": row['Status da Aula'],
                        "Alerta": row['Alerta'],
                        "Observacao": row['Observação'],
                        "Tecnicas": tecnicas_dia.strip() # Salva a técnica atrelada ao aluno
                    })
                    
                    if row['Alerta'] != '🟢 Normal' or (str(row['Observação']).strip() != "" and str(row['Observação']).lower() != "nan"):
                        tem_ocorrencia = True
                        texto_whats += f"👤 *{row['Nome']}* ({row['Turma']})\n"
                        texto_whats += f"Status: {row['Alerta']}\n"
                        texto_whats += f"Obs: {row['Observação']}\n\n"
                
                df_novas = pd.DataFrame(novas_presencas)
                save_attendance(pd.concat([df_att, df_novas], ignore_index=True))
                
                st.success(f"Show! Presença de {len(presentes)} alunos registrada com sucesso!")
                
                if tem_ocorrencia:
                    st.warning("🚨 Foram registradas ocorrências neste treino.")
                    link_escola = f"https://wa.me/553888276956?text={texto_whats.replace(' ', '%20').replace('\n', '%0A')}"
                    st.link_button("📲 Notificar Escola via WhatsApp", link_escola, type="primary")
                else:
                    st.balloons()

        # Histórico do Dia
        st.divider()
        st.subheader(f"⏱️ Histórico do Dia: {data_aula.strftime('%d/%m/%Y')}")
        df_att = get_attendance()
        
        if not df_att.empty:
            df_att_valido = df_att.dropna(subset=['Data'])
            df_dia = df_att_valido[df_att_valido['Data'].dt.date == data_aula].copy()
            
            if not df_dia.empty:
                st.info(f"🥋 **{len(df_dia)} alunos** no tatame hoje.")
                
                # Exibe a coluna de técnicas apenas se ela já existir no banco de dados
                colunas_exibicao = ['Nome', 'Turma', 'Status_Aula', 'Alerta']
                if 'Tecnicas' in df_dia.columns:
                    colunas_exibicao.append('Tecnicas')
                colunas_exibicao.append('Observacao')
                
                st.dataframe(
                    df_dia[colunas_exibicao], 
                    hide_index=True, 
                    use_container_width=True
                )
            else:
                st.write("Nenhuma presença salva para este dia ainda.")
        else:
            st.write("Nenhuma presença salva no sistema.")

    # ==========================================
    # ABA 2: EDITAR E APAGAR PRESENÇAS
    # ==========================================
    with tab_edicao:
        st.subheader("✏️ Corrigir ou Apagar Lançamentos")
        st.markdown("Errou algum lançamento? Selecione a data, escolha o aluno e faça a correção.")
        
        col_data_ed, _ = st.columns([1, 3])
        with col_data_ed:
            data_edicao = st.date_input("📅 Data do Treino para Correção", datetime.now(), key="data_edicao")
            
        df_att_ed = get_attendance()
        
        if not df_att_ed.empty:
            df_att_valido_ed = df_att_ed.dropna(subset=['Data'])
            mascara_dia = df_att_valido_ed['Data'].dt.date == data_edicao
            df_dia_ed = df_att_valido_ed[mascara_dia].copy()
            
            if not df_dia_ed.empty:
                alunos_do_dia = df_dia_ed['Nome'].tolist()
                
                aluno_selecionado = st.selectbox("👤 Selecione o Aluno que treinou neste dia", ["-- Selecione --"] + alunos_do_dia)
                
                if aluno_selecionado != "-- Selecione --":
                    dados_presenca = df_dia_ed[df_dia_ed['Nome'] == aluno_selecionado].iloc[0]
                    
                    st.divider()
                    
                    with st.form("form_edita_presenca"):
                        st.write(f"Gerenciando presença de: **{aluno_selecionado}** ({dados_presenca['Turma']})")
                        
                        try: idx_status = ["Normal", "Experimental", "Visita", "Reposição"].index(dados_presenca['Status_Aula'])
                        except ValueError: idx_status = 0
                        
                        try: idx_alerta = ["🟢 Normal", "🟡 Atenção", "🔴 Grave"].index(dados_presenca.get('Alerta', '🟢 Normal'))
                        except ValueError: idx_alerta = 0
                            
                        novo_status = st.selectbox("Mudar Status da Aula", ["Normal", "Experimental", "Visita", "Reposição"], index=idx_status)
                        novo_alerta = st.selectbox("Mudar Comportamento", ["🟢 Normal", "🟡 Atenção", "🔴 Grave"], index=idx_alerta)
                        
                        # Carrega técnica de forma segura, tratando casos onde a coluna não existe ou tem valores nulos
                        tecnica_atual = str(dados_presenca.get('Tecnicas', '')).replace('nan', '')
                        nova_tecnica = st.text_input("Corrigir Técnicas", value=tecnica_atual)
                        
                        nova_obs = st.text_input("Observação", value=str(dados_presenca.get('Observacao', '')).replace('nan', ''))
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_btn_e, col_btn_del = st.columns(2)
                        
                        btn_atualizar = col_btn_e.form_submit_button("🔄 Atualizar Status e Ocorrência", use_container_width=True)
                        btn_apagar = col_btn_del.form_submit_button("🗑️ Excluir Presença Definitivamente", use_container_width=True)
                        
                        if btn_atualizar:
                            mask = (df_att_ed['Data'].dt.date == data_edicao) & (df_att_ed['Nome'] == aluno_selecionado)
                            df_att_ed.loc[mask, 'Status_Aula'] = novo_status
                            df_att_ed.loc[mask, 'Alerta'] = novo_alerta
                            df_att_ed.loc[mask, 'Tecnicas'] = nova_tecnica
                            df_att_ed.loc[mask, 'Observacao'] = nova_obs
                            
                            save_attendance(df_att_ed)
                            st.success(f"Status de {aluno_selecionado} atualizado com sucesso! Recarregue a página.")
                            
                        if btn_apagar:
                            index_to_drop = df_att_ed[(df_att_ed['Data'].dt.date == data_edicao) & (df_att_ed['Nome'] == aluno_selecionado)].index
                            df_att_ed = df_att_ed.drop(index_to_drop)
                            save_attendance(df_att_ed)
                            st.warning(f"Presença de {aluno_selecionado} excluída. Recarregue a página.")
            else:
                st.info(f"Nenhum treino registrado para o dia {data_edicao.strftime('%d/%m/%Y')}.")
        else:
            st.info("Nenhuma presença registrada no sistema ainda.")