import streamlit as st
import tela_alunos
import tela_chamada
import tela_financeiro
import tela_home

# Configuração inicial da página (deve ser a primeira coisa!)
st.set_page_config(page_title="BJJ Control - Bom Sucesso", page_icon="🥋", layout="wide")

# Título do menu lateral
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8445/8445160.png", width=100) # Ícone de Kimono (opcional)
st.sidebar.title("BJJ Control\nBom Sucesso")
st.sidebar.divider()

# ÚNICO menu de navegação
escolha = st.sidebar.radio(
    "Navegar para:", 
    [
        "🏠 Início (Dashboard)", 
        "📝 Chamada do Treino", 
        "🥋 Gestão de Alunos", 
        "💰 Financeiro"
    ]
)

# Direcionamento das telas
if escolha == "🏠 Início (Dashboard)":
    tela_home.render()
elif escolha == "📝 Chamada do Treino":
    tela_chamada.render()
elif escolha == "🥋 Gestão de Alunos":
    tela_alunos.render()
elif escolha == "💰 Financeiro":
    tela_financeiro.render()