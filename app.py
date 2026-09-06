import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Projeto Bianca", layout="wide")
st.title("Projeto Bianca - Dashboard de Obras")

# Área de carregamento de ficheiro
ficheiro_carregado = st.file_uploader("Arraste o ficheiro Excel (teste.xlsx) para aqui", type=["xlsx"])

if ficheiro_carregado is not None:
    try:
        # Lê o ficheiro diretamente da memória RAM
        df = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        # Processamento para o Gráfico de Gantt
        df_gantt = pd.DataFrame()
        if 'Data de inicio' in df.columns and 'Data de fim' in df.columns:
            df['Data de inicio'] = pd.to_datetime(df['Data de inicio'], errors='coerce')
            df['Data de fim'] = pd.to_datetime(df['Data de fim'], errors='coerce')
            
            if 'Desenho' in df.columns:
                df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
            else:
                df['ID Obra'] = "Desconhecido"
                
            df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])
            
        # Estrutura visual
        tab1, tab2 = st.tabs(["📊 Gráfico de Gantt", "📋 Base de Dados (Tratada)"])
        
        with tab1:
            if not df_gantt.empty:
                fig = px.timeline(
                    df_gantt, 
                    x_start="Data de inicio", 
                    x_end="Data de fim", 
                    y="ID Obra", 
                    color="Situação",
                    hover_name="Desenho",
                    title="Cronograma de Obras Ativas"
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Não existem dados válidos de datas para desenhar o gráfico.")
                
        with tab2:
            st.dataframe(df)
            
    except Exception as e:
        st.error(f"Erro ao processar o ficheiro. Certifique-se que o separador se chama 'Obra (B)'. Erro técnico: {e}")
else:
    st.info("A aguardar o carregamento do ficheiro Excel atualizado.")
