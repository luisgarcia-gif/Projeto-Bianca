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

# ----------------------------------------------------
# ESTADO DA SESSÃO E NAVEGAÇÃO
# ----------------------------------------------------
if 'obra_sel' not in st.session_state:
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
if 'conjunto_sel' not in st.session_state:
    st.session_state['conjunto_sel'] = ""

def reset_filtros():
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
    st.session_state['conjunto_sel'] = ""

# ----------------------------------------------------
# BARRA LATERAL (MENU DE NAVEGAÇÃO COM ÍCONES)
# ----------------------------------------------------
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
    else:
        st.markdown("## **PRF**")
    
    st.markdown("---")
    
    # Menu de Navegação Princpal
    st.subheader("Navegação")
    pagina = st.radio(
        "Selecione o Menu:",
        ["🏠 Início", "📊 Cronograma (Gantt)", "📋 Tabela Detalhada", "📈 Ponto de Situação"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.button("🔄 Reset de Filtros", on_click=reset_filtros, use_container_width=True)

# ----------------------------------------------------
# 🏠 PÁGINA INICIAL (ECRÃ LIMPO)
# ----------------------------------------------------
if pagina == "🏠 Início":
    st.title("🏗️ Portal de Gestão de Obras e Conjuntos - PRF")
    st.markdown("""
    Bem-vindo ao sistema centralizado de monitorização de obras e conjuntos em tempo real.
    
    **Para começar, efetue o carregamento do ficheiro de dados atualizado abaixo:**
    """)
    
    ficheiro_carregado = st.file_uploader("Carregar Base de Dados (teste.xlsx)", type=["xlsx"])
    
    if ficheiro_carregado is not None:
        st.session_state['df_raw'] = pd.read_excel(ficheiro_carregado, sheet_name="Obra (B)", header=1)
        st.success("✅ Ficheiro carregado com sucesso! Utilize o menu lateral para navegar entre as visualizações.")
    else:
        st.info("ℹ️ Aguardando ficheiro Excel para inicializar as análises.")

# ----------------------------------------------------
# PROCESSAMENTO DOS DADOS (SE EXISTIR FICHEIRO)
# ----------------------------------------------------
elif 'df_raw' in st.session_state and st.session_state['df_raw'] is not None:
    df = st.session_state['df_raw'].copy()
    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
    
    # Tratamento de Colunas
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

    # Tradução da coluna "Situação"
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

    # Links para Abrir Ficheiros/Desenhos
    def criar_link_abrir(caminho, arq):
        if pd.notna(caminho) and str(caminho).strip() != "":
            return f"file:///{str(caminho).replace('\\', '/')}"
        elif pd.notna(arq) and str(arq).strip() != "":
            return f"file:///{str(arq)}"
        return None

    df['Abrir'] = [criar_link_abrir(cam, arq) for cam, arq in zip(df_caminhos, df.get('Documento / Arquivo', ['']*len(df)))]

    # Tratamento para o Gantt
    df_gantt = pd.DataFrame()
    if 'Data de inicio' in df.columns and 'Data de fim' in df.columns:
        df['Data de inicio'] = pd.to_datetime(df['Data de inicio'], errors='coerce')
        df['Data de fim'] = pd.to_datetime(df['Data de fim'], errors='coerce')
        
        if 'Desenho' in df.columns:
            df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x else x)
        else:
            df['ID Obra'] = "Desconhecido"
            
        df_gantt = df.dropna(subset=['Data de inicio', 'Data de fim'])

    # FILTROS LATERAIS (Comuns a todas as páginas de análise)
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔍 Filtros de Pesquisa")
        lista_obras = ["Visualização Global (Todas)"] + list(df['ID Obra'].dropna().unique())
        obra_selecionada = st.selectbox("Selecionar Obra:", lista_obras, key='obra_sel')
        termo_conjunto = st.text_input("Pesquisar por Conjunto / Desenho:", key='conjunto_sel')

    # Aplicação de Filtros
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
    if pagina == "📊 Cronograma (Gantt)":
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
                    "Em Execução": "#0097A7",
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
    elif pagina == "📋 Tabela Detalhada":
        st.title("📋 Base de Dados Detalhada de Obras e Desenhos")
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
    elif pagina == "📈 Ponto de Situação":
        st.title("📈 Indicadores e Ponto de Situação")
        
        def contar_estado(keyword):
            return df_filtrado['Situação'].astype(str).str.contains(keyword, case=False, na=False).sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Para Iniciar", contar_estado('Iniciar'))
        col2.metric("Já Iniciadas", contar_estado('Iniciada'))
        col3.metric("Em Execução", contar_estado('Execução'))
        col4.metric("Concluídas", contar_estado('Concluída'))
        col5.metric("Suspensas", contar_estado('Suspensa'))

else:
    st.warning("⚠️ Nenhum ficheiro foi carregado ainda. Aceda ao menu **🏠 Início** para submeter a base de dados.")
