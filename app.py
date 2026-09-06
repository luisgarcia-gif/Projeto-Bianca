import streamlit as st
import pandas as pd
import plotly.express as px

# 6. LAYOUT E CORES DA EMPRESA (PRF)
st.set_page_config(page_title="PRF - Dashboard de Obras", layout="wide", initial_sidebar_state="expanded")

# Injeção de CSS para personalizar as cores para o padrão corporativo (Azul/Branco)
st.markdown("""
    <style>
    /* Cor de fundo principal e texto */
    .stApp {
        background-color: #F4F7F6;
    }
    /* Estilo dos cartões de destaque (Métricas) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border-left: 5px solid #004B87; /* Azul corporativo PRF */
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Títulos */
    h1, h2, h3 {
        color: #004B87 !important;
    }
    /* Ocultar elementos desnecessários do Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 7. LOGOTIPO NA BARRA LATERAL
with st.sidebar:
    # Nota: Substitui o URL abaixo pelo link direto do logotipo da PRF se o tiveres alojado online, 
    # ou carrega um "logo.png" no teu GitHub e escreve st.image("logo.png")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Placeholder_Logo.svg/300px-Placeholder_Logo.svg.png", caption="Insira o Logo PRF no GitHub")
    st.markdown("---")

st.title("Gestão Global de Obras e Conjuntos")

# Área de carregamento de ficheiro
ficheiro_carregado = st.file_uploader("Atualizar Base de Dados (teste.xlsx)", type=["xlsx"])

if ficheiro_carregado is not None:
    try:
        # Carrega o Excel
        df = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        
        # Limpa colunas/linhas 100% vazias
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        # 5. MUDAR OS TÍTULOS DAS COLUNAS (Corrigir o "Unnamed" da tua imagem)
        colunas_renomear = {
            'Unnamed: 0': 'Documento / Arquivo',
            'Unnamed: 1': 'Caminho do Diretório',
            'Unnamed: 2': 'Informação Adicional'
        }
        df = df.rename(columns=colunas_renomear)
        
        # Garante que a coluna de Situação existe para não quebrar o código
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
                
            # Cria a base do Gantt apenas com datas válidas
            df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])

        # ==========================================
        # 1, 2 e 4: BARRA LATERAL DE PESQUISA E FILTROS
        # ==========================================
        st.sidebar.header("Filtros de Pesquisa")
        
        # Filtro Global vs Individual
        lista_obras = ["Visualização Global (Todas)"] + list(df['ID Obra'].dropna().unique())
        obra_selecionada = st.sidebar.selectbox("1 e 2. Selecionar Obra (Global/Individual):", lista_obras)
        
        # 4. Pesquisa por Conjunto (Procura em texto livre dentro do DataFrame)
        termo_conjunto = st.sidebar.text_input("4. Pesquisar por Conjunto / Desenho:")
        
        # Aplicação dos Filtros no df principal e no df_gantt
        df_filtrado = df.copy()
        df_gantt_filtrado = df_gantt.copy()

        if obra_selecionada != "Visualização Global (Todas)":
            df_filtrado = df_filtrado[df_filtrado['ID Obra'] == obra_selecionada]
            if not df_gantt_filtrado.empty:
                df_gantt_filtrado = df_gantt_filtrado[df_gantt_filtrado['ID Obra'] == obra_selecionada]

        if termo_conjunto:
            # Filtra linhas onde o termo inserido existe em qualquer parte da linha (nome do conjunto, ficheiro, etc.)
            mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
            df_filtrado = df_filtrado[mask]
            
            if not df_gantt_filtrado.empty:
                mask_gantt = df_gantt_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
                df_gantt_filtrado = df_gantt_filtrado[mask_gantt]
        
        # ==========================================
        # 3. DESTAQUES (MÉTRICAS / ESTADOS DAS OBRAS)
        # ==========================================
        st.write("### Ponto de Situação (Filtrado)")
        
        # Função auxiliar para procurar palavras-chave nos estados independentemente de como escreveram no Excel
        def contar_estado(estado_keyword):
            return df_filtrado['Situação'].astype(str).str.contains(estado_keyword, case=False, na=False).sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        # Altera as palavras-chave ('iniciar', 'execução', etc.) consoante o que usam efetivamente no vosso Excel
        col1.metric("Para Iniciar", contar_estado('iniciar') or contar_estado('espera'))
        col2.metric("Já Iniciadas", contar_estado('iniciada'))
        col3.metric("Em Execução", contar_estado('execução') or contar_estado('curso'))
        col4.metric("Concluídas", contar_estado('concluída') or contar_estado('fim') or contar_estado('terminada'))
        col5.metric("Suspensas", contar_estado('suspensa') or contar_estado('parada'))

        st.markdown("---")

        # ==========================================
        # VISUALIZAÇÃO DOS DADOS
        # ==========================================
        tab1, tab2 = st.tabs(["📊 Gráfico de Gantt Dinâmico", "📋 Tabela de Dados Detalhada"])
        
        with tab1:
            if not df_gantt_filtrado.empty:
                # Paleta de cores corporativa para o gráfico
                cores_personalizadas = px.colors.qualitative.Set1 
                
                fig = px.timeline(
                    df_gantt_filtrado, 
                    x_start="Data de inicio", 
                    x_end="Data de fim", 
                    y="ID Obra", 
                    color="Situação",
                    hover_name="Documento / Arquivo", # Usa o novo nome da coluna
                    title="Cronograma de Planeamento",
                    color_discrete_sequence=cores_personalizadas
                )
                fig.update_yaxes(autorange="reversed")
                # Define a cor de fundo do gráfico para bater certo com a app
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Nenhum dado com datas válidas encontrado para os filtros atuais.")
                
        with tab2:
            st.dataframe(df_filtrado, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro ao processar o ficheiro. Detalhe técnico: {e}")
else:
    st.info("⬆️ Arraste o ficheiro Excel de Obras para a área acima para gerar a Dashboard PRF.")
