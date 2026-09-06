import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# CSS PERSONALIZADO
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

# ESTADOS DA SESSÃO
if 'pagina_ativa' not in st.session_state:
    st.session_state['pagina_ativa'] = "🏠 Início"
if 'obra_sel' not in st.session_state:
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
if 'conjunto_sel' not in st.session_state:
    st.session_state['conjunto_sel'] = ""
if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None
if 'nome_ficheiro' not in st.session_state:
    st.session_state['nome_ficheiro'] = ""
if 'temp_new_df' not in st.session_state:
    st.session_state['temp_new_df'] = None
if 'temp_new_name' not in st.session_state:
    st.session_state['temp_new_name'] = ""

def ir_para(pagina):
    st.session_state['pagina_ativa'] = pagina

def voltar_ao_inicio_sem_apagar():
    st.session_state['pagina_ativa'] = "🏠 Início"

# FUNÇÃO ROBUSTA PARA LER TODAS AS LINHAS DO EXCEL SEM PERDAS
def carregar_excel_completo(file):
    excel_file = pd.ExcelFile(file)
    aba_alvo = None
    for sheet in excel_file.sheet_names:
        if "obra" in sheet.lower():
            aba_alvo = sheet
            break
    if not aba_alvo:
        aba_alvo = excel_file.sheet_names[0]
        
    # Tenta ler com header na linha 0 (padrão)
    df_temp = pd.read_excel(file, sheet_name=aba_alvo, header=0)
    
    # Se a primeira linha estiver maioritariamente vazia ou for título decorativo, tenta ler com header=1
    if df_temp.columns.str.contains('Unnamed').sum() > len(df_temp.columns) / 2 and len(df_temp) > 0:
        df_alt = pd.read_excel(file, sheet_name=aba_alvo, header=1)
        if len(df_alt) > len(df_temp):
            df_temp = df_alt

    return df_temp, aba_alvo

# BARRA LATERAL
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
    
    st.button("🏠 Voltar ao Início", on_click=voltar_ao_inicio_sem_apagar, use_container_width=True)
    st.markdown("---")

    tem_ficheiro = st.session_state['df_raw'] is not None

    if tem_ficheiro:
        st.subheader("🔍 Filtros de Pesquisa")
        
        df_temp = st.session_state['df_raw'].copy()
        
        # Procura coluna de identificação de obra
        col_obra_nome = None
        for col in ['ID Obra', 'Desenho', 'Referencia', 'Obra']:
            if col in df_temp.columns:
                col_obra_nome = col
                break
                
        if col_obra_nome:
            if col_obra_nome == 'Desenho':
                obras_unicas = df_temp[col_obra_nome].astype(str).apply(lambda x: x.split('-')[0] if '-' in x and x != 'nan' else x).dropna().unique()
            else:
                obras_unicas = df_temp[col_obra_nome].astype(str).dropna().unique()
            lista_obras = ["Visualização Global (Todas)"] + [str(x) for x in obras_unicas if str(x).strip() != "" and str(x).strip() != "nan"]
        else:
            lista_obras = ["Visualização Global (Todas)"]

        st.selectbox("Selecionar Obra:", lista_obras, key='obra_sel')
        st.text_input("Pesquisar por Conjunto / Referência:", key='conjunto_sel')
        
        st.markdown("---")

        st.subheader("Navegação")
        st.button("📊 Progresso e Fases", on_click=ir_para, args=("📊 Progresso e Fases",), use_container_width=True)
        st.button("📋 Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        st.button("📈 Ponto de Situação", on_click=ir_para, args=("📈 Ponto de Situação",), use_container_width=True)
        st.button("📅 Cronograma (Gantt)", on_click=ir_para, args=("📅 Cronograma (Gantt)",), use_container_width=True)

# 🏠 PÁGINA INICIAL
if st.session_state['pagina_ativa'] == "🏠 Início":
    st.title("Portal de Gestão de Obras e Conjuntos")
    st.markdown("### Monitorização em Tempo Real")
    
    ficheiro_carregado = st.file_uploader("Carregar Ficheiro de Obras (.xlsx / .xls)", type=["xlsx", "xls"], key="uploader_input")
    
    if ficheiro_carregado is not None:
        try:
            new_df, aba_alvo = carregar_excel_completo(ficheiro_carregado)
            new_name = ficheiro_carregado.name
            
            if st.session_state['df_raw'] is not None and st.session_state['nome_ficheiro'] != new_name:
                st.session_state['temp_new_df'] = new_df
                st.session_state['temp_new_name'] = new_name
            else:
                st.session_state['df_raw'] = new_df
                st.session_state['nome_ficheiro'] = new_name
                st.session_state['temp_new_df'] = None
        except Exception as e:
            st.error(f"Erro ao ler o ficheiro Excel: {e}")

    if st.session_state['temp_new_df'] is not None:
        st.warning("⚠️ **Novo ficheiro detetado!**")
        st.subheader("Deseja comparar/anexar o ficheiro atual com o novo?")
        
        col_sim, col_nao = st.columns(2)
        with col_sim:
            if st.button("✅ Sim (Anexar/Comparar Ficheiros)", use_container_width=True):
                st.session_state['df_raw'] = pd.concat([st.session_state['df_raw'], st.session_state['temp_new_df']], ignore_index=True)
                st.session_state['nome_ficheiro'] += f" + {st.session_state['temp_new_name']}"
                st.session_state['temp_new_df'] = None
                st.success("Ficheiros anexados com sucesso!")
                st.rerun()
                
        with col_nao:
            if st.button("❌ Não (Substituir pelo Novo)", use_container_width=True):
                st.session_state['df_raw'] = st.session_state['temp_new_df']
                st.session_state['nome_ficheiro'] = st.session_state['temp_new_name']
                st.session_state['temp_new_df'] = None
                st.success("Base de dados substituída com sucesso!")
                st.rerun()

    if st.session_state['df_raw'] is None:
        st.warning("⚠️ **Atenção:** É obrigatório efetuar o carregamento do ficheiro Excel (.xlsx / .xls) para desbloquear a plataforma.")
    else:
        st.info(f"📁 **Ficheiro ativo na memória:** {st.session_state['nome_ficheiro']} | **Total de Registos:** {len(st.session_state['df_raw'])} linhas")
        st.markdown("---")
        st.subheader("Escolha uma das funcionalidades abaixo para continuar a análise:")
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("📊 Progresso e Fases", on_click=ir_para, args=("📊 Progresso e Fases",), use_container_width=True)
        with c2:
            st.button("📋 Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        with c3:
            st.button("📈 Ponto de Situação", on_click=ir_para, args=("📈 Ponto de Situação",), use_container_width=True)
        with c4:
            st.button("📅 Cronograma (Gantt)", on_click=ir_para, args=("📅 Cronograma (Gantt)",), use_container_width=True)

# PROCESSAMENTO DOS DADOS PARA ANÁLISE
if st.session_state['df_raw'] is not None and st.session_state['pagina_ativa'] != "🏠 Início":
    df = st.session_state['df_raw'].copy()
    
    # Remover apenas colunas de sistema sem descartar linhas de dados
    colunas_eliminar = ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Caminho do Diretório', 'Abrir']
    df = df.drop(columns=[col for col in colunas_eliminar if col in df.columns], errors='ignore')

    # Identificação flexível da Obra em todas as linhas
    if 'ID Obra' not in df.columns:
        if 'Desenho' in df.columns:
            df['ID Obra'] = df['Desenho'].astype(str).apply(lambda x: x.split('-')[0] if '-' in x and x != 'nan' else (x if x != 'nan' else "Obra Geral"))
        elif 'Referencia' in df.columns:
            df['ID Obra'] = df['Referencia'].astype(str)
        elif 'Obra' in df.columns:
            df['ID Obra'] = df['Obra'].astype(str)
        else:
            df['ID Obra'] = "Obra Geral"

    df['ID Obra'] = df['ID Obra'].fillna("Obra Geral").astype(str)

    # Estado da Obra
    if 'Situação' in df.columns:
        def traduzir_estado(val):
            s = str(val).lower().strip()
            if val is True or s == 'true' or "conclu" in s:
                return "Obra Concluída"
            elif val is False or s == 'false' or "execu" in s:
                return "Em Execução"
            elif "suspensa" in s or "parada" in s:
                return "Suspensa"
            return "Para Iniciar"
        df['Estado da Obra'] = df['Situação'].apply(traduzir_estado)
    else:
        df['Estado da Obra'] = "Para Iniciar"

    # Receção de Material
    if 'Receção Material' not in df.columns and 'Material' in df.columns:
        df['Receção Material'] = df['Material'].fillna("Pendente")
    elif 'Receção Material' not in df.columns:
        df['Receção Material'] = "Sem informação"

    # Trabalhadores
    if 'Trabalhadores' not in df.columns:
        df['Trabalhadores'] = "Não Atribuído"
    else:
        df['Trabalhadores'] = df['Trabalhadores'].fillna("Não Atribuído")

    # Qualidade
    if 'Qualidade' not in df.columns:
        df['Qualidade'] = "Pendente"

    # FILTRAGEM DINÂMICA
    df_filtrado = df.copy()
    obra_selecionada = st.session_state['obra_sel']
    termo_conjunto = st.session_state['conjunto_sel']

    if obra_selecionada != "Visualização Global (Todas)":
        df_filtrado = df_filtrado[df_filtrado['ID Obra'] == obra_selecionada]

    if termo_conjunto:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    # CÁLCULO DE PROGRESSO POR OBRA (CONSIDERANDO TODAS AS 2000+ LINHAS)
    resumo_obras = []
    for obra, group in df_filtrado.groupby('ID Obra'):
        total_linhas = len(group)
        concluidas = len(group[group['Estado da Obra'] == 'Obra Concluída'])
        pct_executado = round((concluidas / total_linhas) * 100, 1) if total_linhas > 0 else 0
        pct_faltando = round(100 - pct_executado, 1)
        
        resumo_obras.append({
            'ID Obra': obra,
            'Total Linhas/Tarefas': total_linhas,
            'Concluídas': concluidas,
            'Total Executado (%)': pct_executado,
            'Faltando (%)': pct_faltando
        })
    df_resumo = pd.DataFrame(resumo_obras)

    # ----------------------------------------------------
    # VISTAS DE ANÁLISE
    # ----------------------------------------------------

    # 1. PROGRESSO E FASES
    if st.session_state['pagina_ativa'] == "📊 Progresso e Fases":
        st.title("📊 Monitorização do Progresso Executado por Obra")
        st.markdown(f"Exibindo **{len(df_filtrado)}** registos divididos por **{len(df_resumo)}** obras.")
        
        if not df_resumo.empty:
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=df_resumo['ID Obra'],
                x=df_resumo['Total Executado (%)'],
                name='% Executado',
                orientation='h',
                marker=dict(color='#4CAF50'),
                text=df_resumo['Total Executado (%)'].astype(str) + '%',
                textposition='inside'
            ))
            fig_bar.add_trace(go.Bar(
                y=df_resumo['ID Obra'],
                x=df_resumo['Faltando (%)'],
                name='% Faltando',
                orientation='h',
                marker=dict(color='#2196F3'),
                text=df_resumo['Faltando (%)'].astype(str) + '%',
                textposition='inside'
            ))
            fig_bar.update_layout(
                barmode='stack',
                title='Avanço Geral por Obra (%)',
                xaxis=dict(title='Percentagem (%)', range=[0, 100]),
                yaxis=dict(autorange="reversed"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("### Tabela Resumo de Execução")
            st.dataframe(
                df_resumo,
                column_config={
                    "Total Executado (%)": st.column_config.ProgressColumn(
                        "Total Executado (%)",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    ),
                    "Faltando (%)": st.column_config.ProgressColumn(
                        "Faltando (%)",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100
                    )
                },
                use_container_width=True
            )
        else:
            st.warning("Sem dados disponíveis para a seleção atual.")

    # 2. TABELA DETALHADA
    elif st.session_state['pagina_ativa'] == "📋 Tabela Detalhada":
        st.title("📋 Base de Dados Detalhada de Obras")
        st.info(f"A apresentar **{len(df_filtrado)}** linhas totais da base de dados.")
        
        cols_ordenadas = ['ID Obra', 'Estado da Obra', 'Trabalhadores', 'Receção Material', 'Qualidade'] + [c for c in df_filtrado.columns if c not in ['ID Obra', 'Estado da Obra', 'Trabalhadores', 'Receção Material', 'Qualidade']]
        st.dataframe(df_filtrado[cols_ordenadas], use_container_width=True)

    # 3. PONTO DE SITUAÇÃO
    elif st.session_state['pagina_ativa'] == "📈 Ponto de Situação":
        st.title("📈 Indicadores Globais")
        
        def contar_estado(keyword):
            return df_filtrado['Estado da Obra'].astype(str).str.contains(keyword, case=False, na=False).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Para Iniciar", contar_estado('Para Iniciar'))
        c2.metric("Em Execução", contar_estado('Em Execução'))
        c3.metric("Concluídas", contar_estado('Concluída'))
        c4.metric("Suspensas", contar_estado('Suspensa'))

    # 4. CRONOGRAMA DE GANTT (ÚLTIMA OPÇÃO)
    elif st.session_state['pagina_ativa'] == "📅 Cronograma (Gantt)":
        st.title("📅 Cronograma Dinâmico de Obras (Passado, Presente e Futuro)")
        
        if 'Data de inicio' in df_filtrado.columns and 'Data de fim' in df_filtrado.columns:
            df_gantt = df_filtrado.dropna(subset=['Data de inicio', 'Data de fim']).copy()
            df_gantt['Data de inicio'] = pd.to_datetime(df_gantt['Data de inicio'], errors='coerce')
            df_gantt['Data de fim'] = pd.to_datetime(df_gantt['Data de fim'], errors='coerce')
            df_gantt = df_gantt.dropna(subset=['Data de inicio', 'Data de fim'])
            
            if not df_gantt.empty:
                fig_gantt = px.timeline(
                    df_gantt,
                    x_start="Data de inicio",
                    x_end="Data de fim",
                    y="ID Obra",
                    color="Estado da Obra",
                    hover_data=["Trabalhadores", "Receção Material", "Qualidade"],
                    title="Visão Temporal Completa (Passado / Presente / Futuro)",
                    color_discrete_map={
                        "Obra Concluída": "#4CAF50",
                        "Em Execução": "#FFEB3B",
                        "Para Iniciar": "#F44336",
                        "Suspensa": "#D32F2F"
                    }
                )
                fig_gantt.update_yaxes(autorange="reversed")
                fig_gantt.update_layout(legend_title_text='Estado:')
                
                data_minima = df_gantt['Data de inicio'].min() - pd.DateOffset(months=1)
                data_maxima = df_gantt['Data de fim'].max() + pd.DateOffset(months=6)
                fig_gantt.update_xaxes(range=[data_minima, data_maxima])
                
                st.plotly_chart(fig_gantt, use_container_width=True)
            else:
                st.warning("Existem registos na base de dados, mas nenhum possui intervalo de datas válido para desenhar o gráfico de Gantt.")
        else:
            st.warning("As colunas 'Data de inicio' e 'Data de fim' não foram detetadas no ficheiro.")
