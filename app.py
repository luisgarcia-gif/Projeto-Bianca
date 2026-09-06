import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PRF - Dashboard de Obras", layout="wide", initial_sidebar_state="expanded")

# 7. LOGOTIPO NA BARRA LATERAL
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Placeholder_Logo.svg/300px-Placeholder_Logo.svg.png", caption="Logo PRF")
    st.markdown("---")

st.title("Gestão Global de Obras e Conjuntos")

# Área de carregamento de ficheiro
ficheiro_carregado = st.file_uploader("Atualizar Base de Dados (teste.xlsx)", type=["xlsx"])

if ficheiro_carregado is not None:
    try:
        # Carrega o Excel
        df = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        # 5. MUDAR OS TÍTULOS DAS COLUNAS
        colunas_renomear = {
            'Unnamed: 0': 'Documento / Arquivo',
            'Unnamed: 1': 'Caminho do Diretório',
            'Unnamed: 2': 'Informação Adicional'
        }
        df = df.rename(columns=colunas_renomear)
        
        if 'Situação' not in df.columns:
            df['Situação'] = "Não Definido"
        
        # Tratamento de Datas e ID de Obra
        df_gantt = pd.DataFrame()
        if 'Data de inicio' in df.columns and 'Data de fim' in df.columns:
            df['Data de inicio'] = pd.to_datetime(df['Data de inicio'], errors='coerce')
            df['Data de fim'] = pd.to_datetime(df['Data de fim'], errors='coerce')
            
            if 'Desenho' in df.columns:
                df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
            else:
                df['ID Obra'] = "Desconhecido"
                
            df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])

        # 1, 2 e 4: BARRA LATERAL DE PESQUISA E FILTROS
        st.sidebar.header("Filtros de Pesquisa")
        
        lista_obras = ["Visualização Global (Todas)"] + list(df['ID Obra'].dropna().unique())
        obra_selecionada = st.sidebar.selectbox("1 e 2. Selecionar Obra:", lista_obras)
        
        termo_conjunto = st.sidebar.text_input("4. Pesquisar por Conjunto / Desenho:")
        
        df_filtrado = df.copy()
        df_gantt_filtrado = df_gantt.copy()

        if obra_selecionada != "Visualização Global (Todas)":
            df_filtrado = df_filtrado[df_filtrado['ID Obra'] == obra_selecionada]
            if not df_gantt_filtrado.empty:
                df_gantt_filtrado = df_gantt_filtrado[df_gantt_filtrado['ID Obra'] == obra_selecionada]

        if termo_conjunto:
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]
            
            if not df_gantt_filtrado.empty:
                mask_gantt = df_gantt_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
                df_gantt_filtrado = df_gantt_filtrado[mask_gantt]
        
        # 3. DESTAQUES (MÉTRICAS)
        st.write("### Ponto de Situação")
        
        def contar_estado(estado_keyword):
            return df_filtrado['Situação'].astype(str).str.contains(estado_keyword, case=False, na=False).sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        # Nota: Os números aparecerão a zeros até o Excel ter estas palavras escritas na coluna "Situação"
        col1.metric("Para Iniciar", contar_estado('iniciar') or contar_estado('espera'))
        col2.metric("Já Iniciadas", contar_estado('iniciada'))
        col3.metric("Em Execução", contar_estado('execução') or contar_estado('curso'))
        col4.metric("Concluídas", contar_estado('concluída') or contar_estado('fim') or contar_estado('terminada'))
        col5.metric("Suspensas", contar_estado('suspensa') or contar_estado('parada'))

        st.markdown("---")

        # VISUALIZAÇÃO DOS DADOS
        tab1, tab2 = st.tabs(["📊 Gráfico de Gantt Dinâmico", "📋 Tabela de Dados Detalhada"])
        
        with tab1:
            if not df_gantt_filtrado.empty:
                # Cores Corporativas da PRF aplicadas diretamente no gráfico
                fig = px.timeline(
                    df_gantt_filtrado, 
                    x_start="Data de inicio", 
                    x_end="Data de fim", 
                    y="ID Obra", 
                    color="Situação",
                    hover_name="Documento / Arquivo",
                    title="Cronograma de Planeamento",
                    color_discrete_sequence=['#004B87', '#00A1E4', '#8A9097'] # Azul PRF Escuro, Azul Claro, Cinza
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Nenhum dado com datas válidas encontrado para os filtros atuais.")
                
        with tab2:
            st.dataframe(df_filtrado, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao processar o ficheiro. Detalhe técnico: {e}")
else:
    st.info("⬆️ Arraste o ficheiro Excel de Obras para a área acima para gerar a Dashboard PRF.")
