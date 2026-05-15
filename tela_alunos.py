import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_students, get_all_students_raw, save_students

def render():
    st.header("🥋 Gestão de Alunos")
    
    tab1, tab2 = st.tabs(["➕ Novo Aluno", "⚙️ Manutenção de Dados"])
    
    LISTA_TURMAS = [
        "Jardim I", "Jardim II", "1º Ano EF I", "2º Ano EF I", "3º Ano EF I", 
        "4º Ano EF I", "5º Ano EF I", "6º Ano EF II", "7º Ano EF II", "8º Ano EF II", 
        "9º Ano EF II", "1º Ano EM", "2º Ano EM", "3º Ano EM"
    ]
    LISTA_PERIODOS = ["Matutino", "Vespertino", "Integral"]
    LISTA_GRADUACOES = ["Branca", "Cinza", "Amarela", "Laranja", "Verde", "Azul", "Roxa", "Marrom", "Preta"]
    LISTA_PERFIS = ["Normal", "Bolsista", "Com Desconto"]

    # ==========================================
    # ABA 1: NOVO ALUNO
    # ==========================================
    with tab1:
        with st.form("form_novo_aluno", clear_on_submit=True):
            st.subheader("Dados Pessoais e Escolares")
            nome = st.text_input("Nome Completo do Aluno")
            
            colA, colB = st.columns(2)
            with colA:
                data_nasc = st.date_input(
                    "Data de Nascimento", 
                    value=datetime(2015, 1, 1),
                    min_value=datetime(1940, 1, 1),
                    max_value=datetime.now()
                )
            with colB:
                telefone = st.text_input("WhatsApp (Ex: 11999998888)")
            
            c1, c2, c3 = st.columns(3)
            turma = c1.selectbox("Turma", LISTA_TURMAS)
            periodo = c2.selectbox("Período", LISTA_PERIODOS)
            graduacao = c3.selectbox("Graduação (Faixa)", LISTA_GRADUACOES)
            
            st.divider()
            st.subheader("Financeiro")
            c4, c5, c6 = st.columns(3)
            perfil = c4.selectbox("Perfil Financeiro", LISTA_PERFIS)
            valor_base = c5.number_input("Valor Mensalidade Cheia (R$)", min_value=0.0, value=200.0)
            
            desconto = 0.0
            if perfil == "Bolsista":
                desconto = 100.0
                c6.info("Isento (100% de desconto)")
            elif perfil == "Com Desconto":
                desconto = c6.number_input("Desconto Personalizado (%)", min_value=0.0, max_value=100.0, value=0.0)
            
            observacoes = st.text_area("Observações")
            
            if st.form_submit_button("✅ Finalizar Cadastro"):
                if nome:
                    df = get_all_students_raw()
                    new_id = int(df['ID'].max() + 1) if not df.empty else 1
                    
                    new_row = pd.DataFrame([[
                        new_id, nome, data_nasc, telefone, turma, periodo, graduacao, 
                        observacoes, perfil, desconto, valor_base, True
                    ]], columns=df.columns)
                    
                    save_students(pd.concat([df, new_row], ignore_index=True))
                    st.success(f"Sucesso! {nome} adicionado ao sistema.")
                    st.balloons()
                else:
                    st.error("O campo Nome é obrigatório.")

    # ==========================================
    # ABA 2: MANUTENÇÃO (EDIÇÃO DE ALUNO)
    # ==========================================
    with tab2:
        df_ativos = get_students()
        if not df_ativos.empty:
            st.subheader("Alterar ou Desativar Aluno")
            aluno_nome = st.selectbox("Buscar Aluno", df_ativos['Nome'].tolist())
            dados = df_ativos[df_ativos['Nome'] == aluno_nome].iloc[0]
            
            with st.form("form_edicao"):
                enome = st.text_input("Nome", value=dados['Nome'])
                
                # --- Tratamento seguro para Data de Nascimento e Telefone antigos ---
                colA_e, colB_e = st.columns(2)
                
                with colA_e:
                    # Tenta converter a data existente. Se estiver vazia ou der erro, usa 01/01/2015
                    try:
                        raw_date = dados.get('Data_Nascimento', None)
                        if pd.isna(raw_date):
                            data_padrao = datetime(2015, 1, 1).date()
                        elif isinstance(raw_date, str):
                            data_padrao = pd.to_datetime(raw_date).date()
                        else:
                            data_padrao = raw_date.date() if hasattr(raw_date, 'date') else pd.to_datetime(raw_date).date()
                    except:
                        data_padrao = datetime(2015, 1, 1).date()

                    edata_nasc = st.date_input(
                        "Data de Nascimento",
                        value=data_padrao,
                        min_value=datetime(1940, 1, 1),
                        max_value=datetime.now()
                    )
                
                with colB_e:
                    tel_atual = str(dados.get('Telefone', ''))
                    if tel_atual.lower() == 'nan':
                        tel_atual = ""
                    etelefone = st.text_input("WhatsApp", value=tel_atual)

                c1, c2, c3 = st.columns(3)
                try: idx_turma = LISTA_TURMAS.index(dados['Turma'])
                except ValueError: idx_turma = 0
                try: idx_periodo = LISTA_PERIODOS.index(dados['Periodo'])
                except ValueError: idx_periodo = 0
                try: idx_grad = LISTA_GRADUACOES.index(dados['Graduacao'])
                except ValueError: idx_grad = 0
                
                eturma = c1.selectbox("Turma", LISTA_TURMAS, index=idx_turma)
                eperiodo = c2.selectbox("Período", LISTA_PERIODOS, index=idx_periodo)
                egrad = c3.selectbox("Graduação", LISTA_GRADUACOES, index=idx_grad)
                
                st.divider()
                
                try: idx_perfil = LISTA_PERFIS.index(dados['Perfil_Financeiro'])
                except ValueError: idx_perfil = 0
                
                c4, c5, c6 = st.columns(3)
                eperfil = c4.selectbox("Perfil Financeiro", LISTA_PERFIS, index=idx_perfil)
                evalor_base = c5.number_input("Mensalidade Cheia (R$)", value=float(dados['Valor_Base']))
                
                edesconto = 0.0
                if eperfil == "Bolsista":
                    edesconto = 100.0
                    c6.info("Isento (100%)")
                elif eperfil == "Com Desconto":
                    edesconto = c6.number_input("Desconto (%)", value=float(dados['Desconto_Percentual']))
                
                obs_atual = dados['Observacoes']
                if pd.isna(obs_atual):
                    obs_atual = ""
                    
                eobs = st.text_area("Observações", value=str(obs_atual))
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn1, col_btn2 = st.columns(2)
                
                if col_btn1.form_submit_button("✅ Atualizar Dados", use_container_width=True):
                    df_full = get_all_students_raw()
                    
                    df_full['Observacoes'] = df_full['Observacoes'].astype(str)
                    df_full['Nome'] = df_full['Nome'].astype(str)
                    
                    idx = df_full[df_full['ID'] == dados['ID']].index[0]
                    
                    # Atualiza a linha com as novas colunas (Data_Nascimento e Telefone inclusas)
                    df_full.loc[idx, ['ID', 'Nome', 'Data_Nascimento', 'Telefone', 'Turma', 'Periodo', 'Graduacao', 'Observacoes', 'Perfil_Financeiro', 'Desconto_Percentual', 'Valor_Base', 'Ativo']] = [
                        dados['ID'], enome, edata_nasc, etelefone, eturma, eperiodo, egrad, eobs, eperfil, edesconto, evalor_base, True
                    ]
                    
                    df_full['Observacoes'] = df_full['Observacoes'].replace('nan', '')
                    
                    save_students(df_full)
                    st.toast("Dados atualizados!", icon="✅")
                    st.success("Alterações salvas com sucesso. Feche e abra o sistema para ver.")
                
                if col_btn2.form_submit_button("❌ Desativar Aluno", use_container_width=True):
                    df_full = get_all_students_raw()
                    idx = df_full[df_full['ID'] == dados['ID']].index[0]
                    df_full.at[idx, 'Ativo'] = False
                    save_students(df_full)
                    st.warning("Aluno desativado. Recarregue a página.")
        else:
            st.info("Nenhum aluno cadastrado.")