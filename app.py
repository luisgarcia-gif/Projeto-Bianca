import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="PRF - Portal de Gestão de Obras", 
    page_icon="🏗️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# COLOR PALETTE DA PRF (Azul Turquesa Oficial)
PRF_TURQUOISE = "#0097A7"
PRF_DARK = "#006064"
PRF_LIGHT = "#E0F7FA"

# CSS Personalizado para aplicar a cor da PRF e estilo profissional
st.markdown(f"""
    <style>
    /* Estilo do título e headers */
    h1, h2, h3, h4 {{
        color: {PRF_TURQUOISE} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    /* Botões da barra lateral e ações */
    .stButton>button {{
        background-color: {PRF_TURQUOISE};
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {PRF_DARK};
        color: white;
    }}
    /* Cartões de navegação */
    div[data-testid="metric-container"] {{
        background-color: #ffffff;
        border-left: 5px solid {PRF_TURQUOISE};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# ESTADO DA SESSÃO
if 'obra_sel' not in st.session_state:
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
if 'conjunto_sel' not in st.session_state:
    st.session_state['conjunto_sel'] = ""
if 'pagina_ativa' not in st.session_state:
    st.session_state['pagina_ativa'] = "🏠 Início"

def reset_filtros_e_inicio():
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
    st.session_state['conjunto_sel'] = ""
    st.session_state['pagina_ativa'] = "🏠 Início"

# ----------------------------------------------------
# BARRA LATERAL (LOGO E NAVEGAÇÃO CONDICIONAL)
# ----------------------------------------------------
with st.sidebar:
    # 1. LOGÓTIPO DA PRF E AÇÃO DE REGRESSO À PÁGINA PRINCIPAL
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        # Apresentação do Logo PRF em SVG/HTML com a cor exata (#0097A7)
        st.markdown(f"""
            <div style="background-color:{PRF_TURQUOISE}; padding:15px; border-radius:10px; text-align:center;">
                <span style="color:white; font-size:28px; font-weight:bold; letter-spacing:2px;">PRF</span><br>
                <span style="color:white; font-size:10px;">GAS SOLUTIONS</span>
            </div>
        """, unsafe_allow_html=True)
    
    # Clicar no botão abaixo do logo redefini os filtros e volta à página inicial
    st.button("🏠 Voltar ao Início", on_click=reset_filtros_e_inicio, use_container_width=True)
    st.markdown("---")

    # 3. NAVEGAÇÃO APENAS APÓS O UPLOAD DO FICHEIRO
    tem_ficheiro = 'df_raw' in st.session_state and st.session_state['df_raw'] is not None

    if tem_ficheiro:
        st.subheader("Navegação do Portal")
        opcoes_menu = ["🏠 Início", "📊 Cronograma (Gantt)", "📋 Tabela Detalhada", "📈 Ponto de Situação"]
        
        pagina_selecionada = st.radio(
            "Selecione a vista:",
            opcoes_menu,
            index=opcoes_menu.index(st.session_state['pagina_ativa']),
            key="radio_navegacao"
        )
        st.session_state['pagina_ativa'] = pagina_selecionada
        st.markdown("---")
    else:
        st.info("📌 Efetue o carregamento da base de dados para desbloquear os menus de navegação.")

# ----------------------------------------------------
# 🏠 PÁGINA INICIAL (ECRÃ LIMPO E LANDING PAGE)
# ----------------------------------------------------
if st.session_state['pagina_ativa'] == "🏠 Início":
    st.title("Portal de Gestão de Obras e Conjuntos")
    st.markdown("### Bem-vindo à plataforma de monitorização em tempo real")
    
    st.write("Para inicializar as análises e desbloquear os menus interativos, carregue o ficheiro Excel abaixo:")
    
    ficheiro_carregado = st.file_uploader("Carregar Base de Dados (teste.xlsx)", type=["xlsx"])
    
    if ficheiro_carregado is not None:
        st.session_state['df_raw'] = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        st.success("✅ Base de dados carregada com sucesso!")
        
        st.markdown("---")
        st.subheader("Escolha uma das funcionalidades abaixo para começar:")
        
        # 4. BOTÕES INTERATIVOS NA PÁGINA PRINCIPAL
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📊 Abrir Cronograma de Gantt", use_container_width=True):
                st.session_state['pagina_ativa'] = "📊 Cronograma (Gantt)"
                st.rerun()
        with c2:
            if st.button("📋 Abrir Tabela Detalhada", use_container_width=True):
                st.session_state['pagina_ativa'] = "📋 Tabela Detalhada"
                st.rerun()
        with c3:
            if st.button("📈 Abrir Ponto de Situação", use_container_width=True):
                st.session_state['pagina_ativa'] = "📈 Ponto de Situação"
                st.rerun()

# ----------------------------------------------------
# TRATAMENTO DOS DADOS (QUANDO EXISTE FICHEIRO)
# ----------------------------------------------------
if 'df_raw' in st.session_state and st.session_state['df_raw'] is not None and st.session_state['pagina_ativa'] != "🏠 Início":
    df = st.session_state['df_raw'].copy()
    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    
    # Renomear e ocultar colunas
    colunas_renomear = {
        'Unnamed: 0': 'Documento / Arquivo',
        'Unnamed: 2': 'Desenhos'
    }
    df = df.rename(columns=colunas_renomear)
    
    if 'Unnamed: 1' in df.columns:
        df_caminhos = df['Unnamed: 1']
        df = df.drop(columns=['Unnamed: 1'])
    elif 'Caminho do Diretório' in df.columns:
        df_caminhos = df['Caminho do Diretório']
        df = df.drop(columns=['Caminho do Diretório'])
    else:
        df_caminhos = pd.Series([""] * len(df))

    # Traduzir a "Situação"
    if 'Situação' in df.columns:
        def traduzir_estado(val):
            if val is True or str(val).lower() == 'true':
                return "Concluída"
            elif val is False or str(val).lower() == 'false':
                return "Em Execução"
            elif pd.isna(val) or str(val).strip() == "":
                return "Para Iniciar"
            return str(val)
        df['Situação'] = df['Situação'].apply(traduzir_estado)
    else:
        df['Situação'] = "Não Definido"

    # Links para Abrir Desenhos
    def criar_link_abrir(caminho, arq):
        if pd.notna(caminho) and str(caminho).strip() != "":
            return f"file:///{str(caminho).replace('\\', '/')}"
        elif pd.notna(arq) and str(arq).strip() != "":
            return f"file:///{str(arq)}"
        return None

    df['Abrir'] = [criar_link_abrir(cam, arq) for cam, arq in zip(df_caminhos, df.get('Documento / Arquivo', ['']*len(df)))]

    # Tratamento para Gantt
    df_gantt = pd.DataFrame()
    if 'Data de inicio' in df.columns and 'Data de fim' in df.columns:
        df['Data de inicio'] = pd.to_datetime(df['Data de inicio'], errors='coerce')
        df['Data de fim'] = pd.to_datetime(df['Data de fim'], errors='coerce')
        
        if 'Desenho' in df.columns:
            df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
        else:
            df['ID Obra'] = "Desconhecido"
            
        df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])

    # FILTROS LATERAIS DINÂMICOS
    with st.sidebar:
        st.subheader("🔍 Filtros de Pesquisa")
        lista_obras = ["Visualização Global (Todas)"] + list(df['ID Obra'].dropna().unique())
        obra_selecionada = st.selectbox("Selecionar Obra:", lista_obras, key='obra_sel')
        termo_conjunto = st.text_input("Pesquisar Conjunto / Desenho:", key='conjunto_sel')

    # Filtragem
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

    # ----------------------------------------------------
    # 📊 MENU: CRONOGRAMA (GANTT)
    # ----------------------------------------------------
    if st.session_state['pagina_ativa'] == "📊 Cronograma (Gantt)":
        st.title("📊 Cronograma Dinâmico de Obras (Gantt)")
        if not df_gantt_filtrado.empty:
            fig = px.timeline(
                df_gantt_filtrado, 
                x_start="Data de inicio", 
                x_end="Data de fim", 
                y="ID Obra", 
                color="Situação",
                hover_name="Documento / Arquivo",
                title="Planeamento Temporal por Obra",
                color_discrete_map={
                    "Concluída": "#004D40",
                    "Em Execução": PRF_TURQUOISE,
                    "Para Iniciar": "#80DEEA",
                    "Suspensa": "#D32F2F"
                }
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Nenhum registo com datas válidas encontrado para os filtros selecionados.")

    # ----------------------------------------------------
    # 📋 MENU: TABELA DETALHADA
    # ----------------------------------------------------
    elif st.session_state['pagina_ativa'] == "📋 Tabela Detalhada":
        st.title("📋 Base de Dados Detalhada")
        st.dataframe(
            df_filtrado,
            column_config={
                "Abrir": st.column_config.LinkColumn(
                    "Abrir",
                    display_text="📁 Abrir Desenho"
                )
            },
            use_container_width=True
        )

    # ----------------------------------------------------
    # 📈 MENU: PONTO DE SITUAÇÃO / MÉTRICAS
    # ----------------------------------------------------
    elif st.session_state['pagina_ativa'] == "📈 Ponto de Situação":
        st.title("📈 Indicadores e Ponto de Situação")
        
        def contar_estado(keyword):
            return df_filtrado['Situação'].astype(str).str.contains(keyword, case=False, na=False).sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Para Iniciar", contar_estado('Iniciar'))
        col2.metric("Já Iniciadas", contar_estado('Iniciada'))
        col3.metric("Em Execução", contar_estado('Execução'))
        col4.metric("Concluídas", contar_estado('Concluída'))
        col5.metric("Suspensas", contar_estado('Suspensa'))
