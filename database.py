import pandas as pd
import os

STUDENTS_FILE = 'alunos.csv'
ATTENDANCE_FILE = 'presencas.csv'

def get_all_students_raw():
    if os.path.exists(STUDENTS_FILE):
        return pd.read_csv(STUDENTS_FILE)
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
    df.to_csv(STUDENTS_FILE, index=False)

def get_attendance():
    if os.path.exists(ATTENDANCE_FILE):
        df = pd.read_csv(ATTENDANCE_FILE)
        
        # --- AUTO-CORREÇÃO DE COLUNAS ---
        # Garante que novas colunas existam sem quebrar o histórico antigo
        if 'Alerta' not in df.columns:
            df['Alerta'] = '🟢 Normal'
        if 'Observacao' not in df.columns:
            df['Observacao'] = ''
            
        if not df.empty and 'Data' in df.columns:
            df['Data'] = pd.to_datetime(df['Data'], format='mixed', errors='coerce')
        return df
    
    return pd.DataFrame(columns=["Data", "Aluno_ID", "Nome", "Turma", "Status_Aula", "Alerta", "Observacao"])

def save_attendance(df):
    df.to_csv(ATTENDANCE_FILE, index=False)