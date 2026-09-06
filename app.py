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

# PALETA DE CORES PRF
PRF_TURQUOISE = "#0097A7"
PRF_DARK = "#006064"

st.markdown(f"""
    <style>
    h1, h2, h3, h4 {{
        color: {PRF_TURQUOISE} !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
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
    div[data-testid="metric-container"] {{
        background-color: #ffffff;
        border-left: 5px solid {PRF_TURQUOISE};
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# INICIALIZAÇÃO DE ESTADOS
if 'pagina_ativa' not in st.session_state:
    st.session_state['pagina_ativa'] = "🏠 Início"
if 'obra_sel' not in st.session_state:
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
if 'conjunto_sel' not in st.session_state:
    st.session_state['conjunto_sel'] = ""

# FUNÇÕES DE NAVEGAÇÃO
def ir_para(pagina):
    st.session_state['pagina_ativa'] = pagina

def reset_e_inicio():
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
    st.session_state['conjunto_sel'] = ""
    st.session_state['pagina_ativa'] = "🏠 Início"

# ----------------------------------------------------
# BARRA LATERAL (LOGO + FILTROS + NAVEGAÇÃO)
# ----------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        st.markdown(f"""
            <div style="background-color:{PRF_TURQUOISE}; padding:15px; border-radius:10px; text-align:center;">
                <span style="color:white; font-size:28px; font-weight:bold; letter-spacing:2px;">PRF</span><br>
                <span style="color:white; font-size:10px;">GAS SOLUTIONS</span>
            </div>
        """, unsafe_allow_html=True)
    
    st.button("🏠 Voltar ao Início", on_click=reset_e_inicio, use_container_width=True)
    st.markdown("---")

    tem_ficheiro = 'df_raw' in st.session_state and st.session_state['df_raw'] is not None

    if tem_ficheiro:
        # 3. FILTROS PERMANENTES NA BARRA LATERAL
        st.subheader("🔍 Filtros de Pesquisa")
        
        df_temp = st.session_state['df_raw'].copy()
        if 'Desenho' in df_temp.columns:
            df_temp['ID Obra'] = df_temp['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
            lista_obras = ["Visualização Global (Todas)"] + list(df_temp['ID Obra'].dropna().unique())
        else:
            lista_obras = ["Visualização Global (Todas)"]

        st.selectbox("1 e 2. Selecionar Obra:", lista_obras, key='obra_sel')
        st.text_input("4. Pesquisar por Conjunto / Desenho:", key='conjunto_sel')
        
        st.markdown("---")

        st.subheader("Navegação")
        st.button("📊 Cronograma (Gantt)", on_click=ir_para, args=("📊 Cronograma (Gantt)",), use_container_width=True)
        st.button("📋 Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        st.button("📈 Ponto de Situação", on_click=ir_para, args=("📈 Ponto de Situação",), use_container_width=True)

# ----------------------------------------------------
# 🏠 PÁGINA INICIAL
# ----------------------------------------------------
if st.session_state['pagina_ativa'] == "🏠 Início":
    st.title("Portal de Gestão de Obras e Conjuntos")
    st.markdown("### Bem-vindo à plataforma de monitorização em tempo real")
    
    ficheiro_carregado = st.file_uploader("Carregar Base de Dados (teste.xlsx)", type=["xlsx"])
    
    if ficheiro_carregado is not None:
        st.session_state['df_raw'] = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        st.success("✅ Base de dados carregada com sucesso!")

    # 1 e 2. BOTÕES PERMANENTES QUANDO O FICHEIRO JÁ FOI CARREGADO
    if 'df_raw' in st.session_state and st.session_state['df_raw'] is not None:
        st.markdown("---")
        st.subheader("Escolha uma das funcionalidades abaixo para começar:")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("📊 Abrir Cronograma de Gantt", on_click=ir_para, args=("📊 Cronograma (Gantt)",), use_container_width=True)
        with c2:
            st.button("📋 Abrir Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        with c3:
            st.button("📈 Abrir Ponto de Situação", on_click=ir_para, args=("📈 Ponto de Situação",), use_container_width=True)

# ----------------------------------------------------
# PROCESSAMENTO DOS DADOS PARA AS PÁGINAS DE ANÁLISE
# ----------------------------------------------------
if 'df_raw' in st.session_state and st.session_state['df_raw'] is not None and st.session_state['pagina_ativa'] != "🏠 Início":
    df = st.session_state['df_raw'].copy()
    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    
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

    def criar_link_abrir(caminho, arq):
        if pd.notna(caminho) and str(caminho).strip() != "":
            return f"file:///{str(caminho).replace('\\', '/')}"
        elif pd.notna(arq) and str(arq).strip() != "":
            return f"file:///{str(arq)}"
        return None

    df['Abrir'] = [criar_link_abrir(cam, arq) for cam, arq in zip(df_caminhos, df.get('Documento / Arquivo', ['']*len(df)))]

    df_gantt = pd.DataFrame()
    if 'Data de inicio' in df.columns and 'Data de fim' in df.columns:
        df['Data de inicio'] = pd.to_datetime(df['Data de inicio'], errors='coerce')
        df['Data de fim'] = pd.to_datetime(df['Data de fim'], errors='coerce')
        
        if 'Desenho' in df.columns:
            df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
        else:
            df['ID Obra'] = "Desconhecido"
            
        df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])

    # APLICAÇÃO DOS FILTROS DA BARRA LATERAL
    df_filtrado = df.copy()
    df_gantt_filtrado = df_gantt.copy()

    obra_selecionada = st.session_state['obra_sel']
    termo_conjunto = st.session_state['conjunto_sel']

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
    # VISTAS SELECIONADAS
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
