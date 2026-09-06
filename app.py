import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import re

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

# ESTADOS DA SESSÃO E SEGURANÇA DE ROTAS
vistas_validas = ["🏠 Início", "📊 Progresso e Fases", "📋 Tabela Detalhada", "📈 Indicadores Globais & Tempos"]

if 'pagina_ativa' not in st.session_state or st.session_state['pagina_ativa'] not in vistas_validas:
    st.session_state['pagina_ativa'] = "🏠 Início"

if 'obra_sel' not in st.session_state:
    st.session_state['obra_sel'] = "Visualização Global (Todas)"
if 'conjunto_sel' not in st.session_state:
    st.session_state['conjunto_sel'] = ""
if 'trabalhador_sel' not in st.session_state:
    st.session_state['trabalhador_sel'] = ""
if 'df_raw' not in st.session_state:
    st.session_state['df_raw'] = None
if 'df_resumo_pct' not in st.session_state:
    st.session_state['df_resumo_pct'] = None
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

# FUNÇÃO DE CARREGAMENTO DO FICHEIRO EXCEL
def carregar_excel_completo(file):
    excel_file = pd.ExcelFile(file)
    
    df_res_pct = None
    if 'Resumo %' in excel_file.sheet_names:
        df_res_pct = pd.read_excel(file, sheet_name='Resumo %')
        df_res_pct = df_res_pct.dropna(how='all').dropna(axis=1, how='all')
        if 'Obras' in df_res_pct.columns:
            df_res_pct['ID Obra'] = df_res_pct['Obras'].astype(str).str.strip()

    dfs = []
    abas_relevantes = [s for s in excel_file.sheet_names if any(k in s.lower() for k in ['fabrico', 'montagem', 'obra'])]
    if not abas_relevantes:
        abas_relevantes = excel_file.sheet_names

    for sheet in abas_relevantes:
        df_prev = pd.read_excel(file, sheet_name=sheet, header=None, nrows=20)
        header_idx = 0
        max_matches = 0
        palavras_chave = ['desenho', 'desenhos', 'situação', 'situacao', 'trabalhadores', 'obra', 'referencia', 'material', 'qualidade', 'name', 'tempo estimado']
        
        for idx, row in df_prev.iterrows():
            row_cells = [str(x).lower().strip() for x in row.values if pd.notna(x)]
            matches = sum(1 for p in palavras_chave if any(p in cell for cell in row_cells))
            if matches > max_matches:
                max_matches = matches
                header_idx = idx
                
        df_sheet = pd.read_excel(file, sheet_name=sheet, header=header_idx)
        df_sheet['Fase Operacional'] = sheet
        dfs.append(df_sheet)
        
    df_consolidado = pd.concat(dfs, ignore_index=True)
    return df_consolidado, df_res_pct

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
        
        cols_des = [c for c in df_temp.columns if any(k in str(c).lower() for k in ['desenho', 'name', 'referencia'])]
        if cols_des:
            col_ref = cols_des[0]
            df_temp['ID Obra'] = df_temp[col_ref].astype(str).apply(lambda x: str(x).split('-')[0] if '-' in str(x) and str(x) != 'nan' else str(x))
            obras_unicas = [str(x).strip() for x in df_temp['ID Obra'].unique() if str(x).strip() not in ["", "nan", "None", "l"]]
            lista_obras = ["Visualização Global (Todas)"] + sorted(list(set(obras_unicas)))
        else:
            lista_obras = ["Visualização Global (Todas)"]

        # PESQUISAS
        st.text_input("🔍 Pesquisar Obra (ex: HY25003 ou 25003):", key='obra_sel')
        st.text_input("📦 Pesquisar por Conjunto / Referência:", key='conjunto_sel')
        st.text_input("👷 Pesquisar Trabalhador / Soldador:", key='trabalhador_sel')
        
        st.markdown("---")

        st.subheader("Navegação")
        st.button("📊 Progresso e Fases", on_click=ir_para, args=("📊 Progresso e Fases",), use_container_width=True)
        st.button("📋 Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        st.button("📈 Indicadores Globais & Tempos", on_click=ir_para, args=("📈 Indicadores Globais & Tempos",), use_container_width=True)

# 🏠 PÁGINA INICIAL
if st.session_state['pagina_ativa'] == "🏠 Início":
    st.title("Portal de Gestão de Obras e Conjuntos")
    st.markdown("### Monitorização em Tempo Real")
    
    ficheiro_carregado = st.file_uploader("Carregar Ficheiro de Obras (.xlsx / .xls)", type=["xlsx", "xls"], key="uploader_input")
    
    if ficheiro_carregado is not None:
        try:
            new_df, new_res_pct = carregar_excel_completo(ficheiro_carregado)
            new_name = ficheiro_carregado.name
            
            if st.session_state['df_raw'] is not None and st.session_state['nome_ficheiro'] != new_name:
                st.session_state['temp_new_df'] = new_df
                st.session_state['temp_new_name'] = new_name
            else:
                st.session_state['df_raw'] = new_df
                st.session_state['df_resumo_pct'] = new_res_pct
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
        st.info(f"📁 **Ficheiro ativo:** {st.session_state['nome_ficheiro']} | **Total de Registos Consolidados:** {len(st.session_state['df_raw'])} linhas")
        st.markdown("---")
        st.subheader("Escolha uma das funcionalidades abaixo para continuar a análise:")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.button("📊 Progresso e Fases", on_click=ir_para, args=("📊 Progresso e Fases",), use_container_width=True)
        with c2:
            st.button("📋 Tabela Detalhada", on_click=ir_para, args=("📋 Tabela Detalhada",), use_container_width=True)
        with c3:
            st.button("📈 Indicadores Globais & Tempos", on_click=ir_para, args=("📈 Indicadores Globais & Tempos",), use_container_width=True)

# PROCESSAMENTO DOS DADOS PARA ANÁLISE
if st.session_state['df_raw'] is not None and st.session_state['pagina_ativa'] != "🏠 Início":
    df = st.session_state['df_raw'].copy()
    
    colunas_eliminar = ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Abrir', 'nom2', 'Personalizado']
    df = df.drop(columns=[col for col in colunas_eliminar if col in df.columns], errors='ignore')

    # Identificação do ID da Obra
    col_desenho = [c for c in df.columns if any(k in str(c).lower() for k in ['desenho', 'desenhos', 'name', 'referencia'])]
    if col_desenho:
        df['Desenho_Ref'] = df[col_desenho[0]]
        df['ID Obra'] = df[col_desenho[0]].astype(str).apply(lambda x: str(x).split('-')[0] if '-' in str(x) and str(x) != 'nan' else (str(x) if str(x) != 'nan' else "Obra Geral"))
    else:
        df['Desenho_Ref'] = "Sem Referência"
        df['ID Obra'] = "Obra Geral"

    df['ID Obra'] = df['ID Obra'].replace(['nan', 'None', 'l'], 'Obra Geral').fillna("Obra Geral")

    # Mapeamento de Estado
    col_sit = [c for c in df.columns if 'situa' in str(c).lower()]
    if col_sit:
        def traduzir_estado(val):
            s = str(val).lower().strip()
            if val is True or s == 'true' or "conclu" in s:
                return "Obra Concluída"
            elif val is False or s == 'false' or "execu" in s:
                return "Em Execução"
            elif "suspensa" in s or "parada" in s:
                return "Suspensa"
            return "Para Iniciar"
        df['Estado da Obra'] = df[col_sit[0]].apply(traduzir_estado)
    else:
        df['Estado da Obra'] = "Para Iniciar"

    # Mapeamento de Trabalhadores
    col_trab = [c for c in df.columns if 'trabalha' in str(c).lower()]
    if col_trab:
        df['Trabalhadores'] = df[col_trab[0]].fillna("Não Atribuído")
    else:
        df['Trabalhadores'] = "Não Atribuído"

    # Receção de Material e Qualidade
    col_mat = [c for c in df.columns if 'material' in str(c).lower() or 'rece' in str(c).lower()]
    df['Receção Material'] = df[col_mat[0]].fillna("Sem informação") if col_mat else "Sem informação"

    col_qual = [c for c in df.columns if 'qualid' in str(c).lower()]
    df['Qualidade'] = df[col_qual[0]].fillna("Pendente") if col_qual else "Pendente"

    # FILTRAGEM DINÂMICA
    df_filtrado = df.copy()
    obra_termo = str(st.session_state['obra_sel']).strip()
    termo_conjunto = str(st.session_state['conjunto_sel']).strip()
    trabalhador_termo = str(st.session_state['trabalhador_sel']).strip()

    # Filtro por Obra
    if obra_termo and obra_termo != "Visualização Global (Todas)":
        numeros_termo = re.sub(r'\D', '', obra_termo)
        def corresponder_obra(val):
            val_str = str(val).strip()
            if obra_termo.lower() in val_str.lower(): return True
            val_num = re.sub(r'\D', '', val_str)
            if numeros_termo and len(numeros_termo) >= 2 and numeros_termo in val_num: return True
            return False
            
        df_filtrado = df_filtrado[df_filtrado['ID Obra'].apply(corresponder_obra)]

    # Filtro por Conjunto
    if termo_conjunto:
        mask = df_filtrado.astype(str).apply(lambda x: x.str.contains(termo_conjunto, case=False, na=False)).any(axis=1)
        df_filtrado = df_filtrado[mask]

    # Filtro por Trabalhador
    if trabalhador_termo:
        mask_trab = df_filtrado['Trabalhadores'].astype(str).str.contains(trabalhador_termo, case=False, na=False)
        df_filtrado = df_filtrado[mask_trab]

    # ----------------------------------------------------
    # VISTAS DE ANÁLISE EXCLUSIVAS
    # ----------------------------------------------------

    # 1. PROGRESSO E FASES
    if st.session_state['pagina_ativa'] == "📊 Progresso e Fases":
        st.title("📊 Monitorização do Progresso e Fases por Obra")
        
        if st.session_state['df_resumo_pct'] is not None and not trabalhador_termo:
            df_pct = st.session_state['df_resumo_pct'].copy()
            if obra_termo and obra_termo != "Visualização Global (Todas)":
                numeros_t = re.sub(r'\D', '', obra_termo)
                def m_pct(v):
                    vs = str(v).lower()
                    vn = re.sub(r'\D', '', str(v))
                    return (obra_termo.lower() in vs) or (numeros_t and len(numeros_t) >= 2 and numeros_t in vn)
                df_pct = df_pct[df_pct['ID Obra'].apply(m_pct)]
                
            st.markdown("### Percentagem de Conclusão por Fase (Fabrico / Montagem / Obra)")
            
            # Gráfico de Barras com Cores Melhoradas
            fig_fases = go.Figure()
            if 'Fabrico' in df_pct.columns:
                fig_fases.add_trace(go.Bar(y=df_pct['ID Obra'], x=df_pct['Fabrico']*100, name='Fabrico (%)', orientation='h', marker_color='#9C27B0')) # Roxo
            if 'Montagem' in df_pct.columns:
                fig_fases.add_trace(go.Bar(y=df_pct['ID Obra'], x=df_pct['Montagem']*100, name='Montagem (%)', orientation='h', marker_color='#FF9800')) # Laranja
            if 'Obra' in df_pct.columns:
                fig_fases.add_trace(go.Bar(y=df_pct['ID Obra'], x=df_pct['Obra']*100, name='Obra (%)', orientation='h', marker_color='#4CAF50')) # Verde
                
            fig_fases.update_layout(
                barmode='group',
                title='Avanço por Fase de Produção (%)',
                xaxis=dict(title='Conclusão (%)', range=[0, 100]),
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_fases, use_container_width=True)

            st.markdown("### Tabela Detalhada de Progresso por Fase")
            
            # ELIMINA AS COLUNAS "MONTAGEM" E "OBRA" DA TABELA VISUAL
            cols_table_pct = [c for c in ['Obras', 'Fabrico', 'Total executado', 'Faltando'] if c in df_pct.columns]
            
            config_cols = {}
            for col_p in cols_table_pct:
                if col_p != 'Obras':
                    config_cols[col_p] = st.column_config.ProgressColumn(
                        col_p,
                        format="%.0f%%" if df_pct[col_p].max() > 1 else "%.1f%%",
                        min_value=0,
                        max_value=100 if df_pct[col_p].max() > 1 else 1.0
                    )
            
            df_pct_display = df_pct[cols_table_pct].copy()
            st.dataframe(df_pct_display, column_config=config_cols, use_container_width=True)
            
        else:
            if trabalhador_termo:
                st.info(f"O cálculo de progresso reflete as tarefas alocadas ao colaborador: **{trabalhador_termo}**")
            
            resumo_obras = []
            for obra, group in df_filtrado.groupby('ID Obra'):
                if obra in ["Obra Geral", "l", "nan"]: continue
                tot = len(group)
                conc = len(group[group['Estado da Obra'] == 'Obra Concluída'])
                pct_ex = round((conc / tot) * 100, 1) if tot > 0 else 0
                resumo_obras.append({
                    'Obras': obra,
                    'Total Tarefas': tot,
                    'Concluídas': conc,
                    'Total executado': pct_ex,
                    'Faltando': round(100 - pct_ex, 1)
                })
            df_res = pd.DataFrame(resumo_obras)
            st.dataframe(df_res, use_container_width=True)

    # 2. TABELA DETALHADA
    elif st.session_state['pagina_ativa'] == "📋 Tabela Detalhada":
        st.title("📋 Base de Dados Detalhada de Obras")
        st.info(f"A apresentar **{len(df_filtrado)}** linhas da base de dados consolidada.")
        
        cols_ordenadas = ['ID Obra', 'Desenho_Ref', 'Fase Operacional', 'Estado da Obra', 'Trabalhadores', 'Receção Material', 'Qualidade'] + [c for c in df_filtrado.columns if c not in ['ID Obra', 'Desenho_Ref', 'Fase Operacional', 'Estado da Obra', 'Trabalhadores', 'Receção Material', 'Qualidade']]
        
        df_display_detalhe = df_filtrado[cols_ordenadas].drop(columns=['ID Obra'], errors='ignore')
        st.dataframe(df_display_detalhe, use_container_width=True)

    # 3. INDICADORES GLOBAIS & TEMPOS DE EXECUÇÃO
    elif st.session_state['pagina_ativa'] == "📈 Indicadores Globais & Tempos":
        st.title("📈 Indicadores Globais e Tempos de Execução")
        
        def contar_estado(keyword):
            return df_filtrado['Estado da Obra'].astype(str).str.contains(keyword, case=False, na=False).sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Para Iniciar", contar_estado('Para Iniciar'))
        m2.metric("Em Execução", contar_estado('Em Execução'))
        m3.metric("Concluídas", contar_estado('Concluída'))
        m4.metric("Suspensas", contar_estado('Suspensa'))

        st.markdown("---")
        st.subheader("⏱️ Tempos de Execução das Obras (Planeado vs Realizado)")
        
        cols_tempos = [c for c in df_filtrado.columns if any(k in str(c).lower() for k in ['desenho_ref', 'situação', 'estado', 'tempo', 'data', 'trabalhad', 'fase'])]
        
        df_exibicao_tempos = df_filtrado[cols_tempos].copy()
        
        col_t_est = [c for c in cols_tempos if 'tempo est' in str(c).lower()]
        col_d_ini = [c for c in cols_tempos if 'inicio' in str(c).lower() or 'início' in str(c).lower()]
        
        if col_t_est and col_d_ini:
            df_exibicao_tempos = df_exibicao_tempos.dropna(subset=[col_t_est[0], col_d_ini[0]], how='all')

        st.info(f"A apresentar os prazos correspondentes a **{len(df_exibicao_tempos)}** tarefas filtradas.")
        
        st.dataframe(df_exibicao_tempos, use_container_width=True)
