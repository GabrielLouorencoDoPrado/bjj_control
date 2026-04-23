import streamlit as st
import pandas as pd

# Cria a conexão com o Supabase usando o cofre de segredos do Streamlit
def get_connection():
    return st.connection("supabase", type="sql")

def get_all_students_raw():
    conn = get_connection()
    try:
        # Tenta ler a tabela direto da nuvem
        df = pd.read_sql_table("alunos", con=conn.engine)
        return df
    except Exception:
        # Se a tabela não existir (primeiro uso), cria a estrutura na memória
        return pd.DataFrame(columns=[
            "ID", "Nome", "Data_Nascimento", "Telefone", "Turma", "Periodo", 
            "Graduacao", "Observacoes", "Perfil_Financeiro", "Desconto_Percentual", 
            "Valor_Base", "Ativo"
        ])

def get_students():
    df = get_all_students_raw()
    if not df.empty:
        return df[df['Ativo'] == True]
    return df

def save_students(df):
    conn = get_connection()
    # Grava a tabela inteira no Supabase (Cria a tabela se ela não existir)
    df.to_sql("alunos", con=conn.engine, if_exists="replace", index=False)

def get_attendance():
    conn = get_connection()
    try:
        df = pd.read_sql_table("presencas", con=conn.engine)
        
        # --- AUTO-CORREÇÃO DE COLUNAS ---
        if 'Alerta' not in df.columns:
            df['Alerta'] = '🟢 Normal'
        if 'Observacao' not in df.columns:
            df['Observacao'] = ''
            
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], format='mixed', errors='coerce')
        return df
    except Exception:
        return pd.DataFrame(columns=["Data", "Aluno_ID", "Nome", "Turma", "Status_Aula", "Alerta", "Observacao"])

def save_attendance(df):
    conn = get_connection()
    df.to_sql("presencas", con=conn.engine, if_exists="replace", index=False)