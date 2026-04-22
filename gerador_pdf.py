from fpdf import FPDF
import pandas as pd
import os

def criar_relatorio_escola(df_att, mes, ano):
    df_mes = df_att[(df_att['Data'].dt.month == mes) & (df_att['Data'].dt.year == ano)].copy()
    if df_mes.empty: return None

    df_normais = df_mes[df_mes['Status_Aula'].isin(['Normal', 'Reposição'])]
    contagem_normais = df_normais.groupby('Nome').size()
    alunos_matriculados = contagem_normais[contagem_normais >= 2].index.tolist()

    if not alunos_matriculados: return None

    df_relatorio = df_mes[df_mes['Nome'].isin(alunos_matriculados)].sort_values(by=['Nome', 'Data'])

    pdf = FPDF()
    pdf.add_page()
    
    # Logo
    caminho_logo = 'logo.png'
    if os.path.exists(caminho_logo):
        pdf.image(caminho_logo, x=85, y=10, w=40)
        pdf.ln(45)
    else:
        pdf.ln(10)
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio Mensal de Presenca", ln=True, align='C')
    pdf.set_font("Arial", 'I', 11)
    pdf.cell(200, 6, txt="Bom Sucesso - Escola Montessoriana", ln=True, align='C')
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 6, txt=f"Mes de Referencia: {mes:02d}/{ano}", ln=True, align='C')
    pdf.cell(200, 6, txt="Professores: Gabriel Lourenco do Prado e Tananda Maria Goncalves Martins", ln=True, align='C')
    pdf.ln(10)

    # Lista de Alunos
    for aluno in sorted(alunos_matriculados):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 8, txt=f"Aluno: {aluno}", ln=True)
        
        aulas_aluno = df_relatorio[df_relatorio['Nome'] == aluno]
        pdf.set_font("Arial", '', 10)
        
        for _, row in aulas_aluno.iterrows():
            data_str = row['Data'].strftime("%d/%m/%Y")
            status = row['Status_Aula']
            alerta = row.get('Alerta', '🟢 Normal')
            obs = row.get('Observacao', '')

            # Linha da Aula
            linha = f"   - {data_str} | Status: {status} | Comportamento: {alerta}"
            pdf.cell(200, 6, txt=linha, ln=True)
            
            # Se houver observação, imprime abaixo em itálico
            if pd.notna(obs) and str(obs).strip() != "" and str(obs).lower() != "nan":
                pdf.set_font("Arial", 'I', 9)
                pdf.set_text_color(150, 0, 0) # Cor levemente avermelhada para destaque
                pdf.multi_cell(180, 5, txt=f"     >> Ocorrencia: {obs}")
                pdf.set_text_color(0, 0, 0) # Volta para o preto
                pdf.set_font("Arial", '', 10)
            
        pdf.ln(4)

    return pdf.output(dest='S').encode('latin-1')