import pandas as pd
from sqlalchemy import create_engine

# 1. Cole aqui o link que você pegou no Supabase (com a sua senha)
URL_CONEXAO = "postgresql://postgres:1BakaKoroshi26@db.bvzlnqimcctkacfcmunq.supabase.co:5432/postgres"

def migrar():
    engine = create_engine(URL_CONEXAO)
    
    print("🚀 Iniciando migração...")

    # Migrar Alunos
    try:
        df_alunos = pd.read_csv('alunos.csv')
        df_alunos.to_sql('alunos', con=engine, if_exists='replace', index=False)
        print(f"✅ {len(df_alunos)} alunos transferidos com sucesso!")
    except FileNotFoundError:
        print("⚠️ Arquivo alunos.csv não encontrado. Pulando...")

    # Migrar Presenças
    try:
        df_presencas = pd.read_csv('presencas.csv')
        df_presencas.to_sql('presencas', con=engine, if_exists='replace', index=False)
        print(f"✅ {len(df_presencas)} registros de presença transferidos!")
    except FileNotFoundError:
        print("⚠️ Arquivo presencas.csv não encontrado. Pulando...")

    print("\n🏆 Migração concluída! Os dados já estão na nuvem.")

if __name__ == "__main__":
    migrar()