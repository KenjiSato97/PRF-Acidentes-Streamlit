import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import gzip

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Acidentes Rodoviários",
    page_icon="🚗",
    layout="wide"
)

with gzip.open('acidentes2024.csv.gz', 'rb') as f:
    data = pd.read_csv(f, encoding='latin1', sep=';', decimal=',')

# Função para carregar os dados
@st.cache_data
def load_data():
    df = data.copy()
    # Verificar se a coluna 'data_inversa' existe
    if 'data_inversa' in df.columns:
        # Conversão de data_inversa para datetime
        df['data'] = pd.to_datetime(df['data_inversa'], format='%Y-%m-%d', errors='coerce')
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['mes_nome'] = df['data'].dt.month_name()
    else:
        st.error("A coluna 'data_inversa' não foi encontrada no arquivo.")
        st.stop()
    return df

# Carregando os dados
try:
    df = load_data()
    st.success("Dados carregados com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.info("Por favor, faça o upload do arquivo CSV:")
    uploaded_file = st.file_uploader("Escolha o arquivo CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        # Conversão de data_inversa para datetime
        df['data'] = pd.to_datetime(df['data_inversa'], format='%Y-%m-%d', errors='coerce')
        df['ano'] = df['data'].dt.year
        df['mes'] = df['data'].dt.month
        df['mes_nome'] = df['data'].dt.month_name()
        st.success("Dados carregados com sucesso!")
    else:
        st.stop()

# Título do Dashboard
st.title("📊 Dashboard de Análise de Acidentes Rodoviários")
st.markdown("---")

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro de período
anos_disponiveis = sorted(df['ano'].dropna().unique().tolist())
ano_selecionado = st.sidebar.multiselect("Selecione o(s) Ano(s):", anos_disponiveis, default=anos_disponiveis[-1:])

# Filtro de UF
ufs_disponiveis = sorted(df['uf'].dropna().unique().tolist())
uf_selecionada = st.sidebar.multiselect("Selecione o(s) Estado(s):", ufs_disponiveis, default=[])

# Filtro de tipo de acidente
tipos_acidentes = sorted(df['tipo_acidente'].dropna().unique().tolist())
tipo_acidente_selecionado = st.sidebar.multiselect("Selecione o(s) Tipo(s) de Acidente:", tipos_acidentes, default=[])

# Aplicando os filtros
filtered_df = df.copy()

if ano_selecionado:
    filtered_df = filtered_df[filtered_df['ano'].isin(ano_selecionado)]
if uf_selecionada:
    filtered_df = filtered_df[filtered_df['uf'].isin(uf_selecionada)]
if tipo_acidente_selecionado:
    filtered_df = filtered_df[filtered_df['tipo_acidente'].isin(tipo_acidente_selecionado)]

# Resumo dos dados filtrados
st.header("Resumo dos Dados")
col1, col2, col3, col4 = st.columns(4)

# Contagem total de acidentes
total_acidentes = filtered_df['id'].nunique()
col1.metric("Total de Acidentes", f"{total_acidentes:,}")

# Contagem total de vítimas fatais
total_mortos = filtered_df['mortos'].sum()
col2.metric("Total de Vítimas Fatais", f"{int(total_mortos):,}")

# Contagem total de feridos
total_feridos = filtered_df['feridos_leves'].sum() + filtered_df['feridos_graves'].sum()
col3.metric("Total de Feridos", f"{int(total_feridos):,}")

# Estados com maior incidência
estado_mais_acidentes = filtered_df['uf'].value_counts().idxmax() if not filtered_df.empty else "N/A"
col4.metric("Estado com Mais Acidentes", estado_mais_acidentes)

# Layout em abas
tab1, tab2, tab3, tab4 = st.tabs(["Análise Temporal", "Análise Geográfica", "Causas e Tipos", "Perfil das Vítimas"])

with tab1:
    st.header("Análise Temporal dos Acidentes")
    
    # Análise por mês e ano
    acidentes_por_mes = filtered_df.groupby(['ano', 'mes']).size().reset_index(name='contagem')
    
    # Gráfico de linhas para evolução mensal
    fig = px.line(acidentes_por_mes, x='mes', y='contagem', color='ano',
                  title='Evolução Mensal de Acidentes por Ano',
                  labels={'contagem': 'Número de Acidentes', 'mes': 'Mês', 'ano': 'Ano'},
                  markers=True,
                  line_shape='linear')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Análise por dia da semana
    col1, col2 = st.columns(2)
    
    with col1:
        # Ordenar dias da semana corretamente
        dias_ordem = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 
                      'sexta-feira', 'sábado' ]
        dias_df = filtered_df['dia_semana'].value_counts().reindex(dias_ordem).fillna(0).reset_index()
        dias_df.columns = ['Dia da Semana', 'Contagem']
        
        fig = px.bar(dias_df, x='Dia da Semana', y='Contagem',
                     title='Acidentes por Dia da Semana',
                     color='Contagem', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Acidentes por horário
        # Convertendo horário para hora do dia (0-23)
        filtered_df['hora'] = pd.to_datetime(filtered_df['horario'], format='%H:%M:%S', errors='coerce').dt.hour
        horas_df = filtered_df['hora'].value_counts().sort_index().reset_index()
        horas_df.columns = ['Hora', 'Contagem']
        
        fig = px.bar(horas_df, x='Hora', y='Contagem',
                     title='Acidentes por Hora do Dia',
                     color='Contagem', color_continuous_scale='Viridis')
        fig.update_xaxes(tickvals=list(range(0, 24)))
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Análise Geográfica")
    
    # Mapa de acidentes
    st.subheader("Distribuição Geográfica dos Acidentes")
    
    # Filtrar dados com coordenadas válidas
    filtered_df['latitude'] = pd.to_numeric(filtered_df['latitude'], errors='coerce')
    filtered_df['longitude'] = pd.to_numeric(filtered_df['longitude'], errors='coerce')
    map_data = filtered_df[['latitude', 'longitude']].dropna()
    # Limitar a 5000 pontos para performance
    if len(map_data) > 5000:
        map_data = map_data.sample(5000, random_state=42)
    
    if not map_data.empty:
        st.map(map_data)
    else:
        st.warning("Não há dados de coordenadas disponíveis para exibir no mapa.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top 10 UFs com mais acidentes
        top_ufs = filtered_df['uf'].value_counts().head(10).reset_index()
        top_ufs.columns = ['UF', 'Contagem']
        
        fig = px.bar(top_ufs, x='UF', y='Contagem',
                     title='Top 10 Estados com Mais Acidentes',
                     color='Contagem', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top 10 municípios com mais acidentes
        top_municipios = filtered_df['municipio'].value_counts().head(10).reset_index()
        top_municipios.columns = ['Município', 'Contagem']
        
        fig = px.bar(top_municipios, x='Contagem', y='Município',
                     title='Top 10 Municípios com Mais Acidentes',
                     color='Contagem', color_continuous_scale='Reds',
                     orientation='h')
        st.plotly_chart(fig, use_container_width=True)
    
    # Acidentes por BR
    if 'br' in filtered_df.columns:
        top_brs = filtered_df['br'].value_counts().head(10).reset_index()
        top_brs.columns = ['BR', 'Contagem']
        
        fig = px.bar(top_brs, x='BR', y='Contagem',
                     title='Top 10 BRs com Mais Acidentes',
                     color='Contagem', color_continuous_scale='Oranges')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Causas e Tipos de Acidentes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Principais causas de acidentes
        top_causas = filtered_df['causa_principal'].value_counts().head(10).reset_index()
        top_causas.columns = ['Causa Principal', 'Contagem']
        
        fig = px.bar(top_causas, x='Contagem', y='Causa Principal',
                     title='Top 10 Causas de Acidentes',
                     color='Contagem', color_continuous_scale='Blues',
                     orientation='h')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tipos de acidentes
        top_tipos = filtered_df['tipo_acidente'].value_counts().head(10).reset_index()
        top_tipos.columns = ['Tipo de Acidente', 'Contagem']
        
        fig = px.pie(top_tipos, values='Contagem', names='Tipo de Acidente',
                     title='Distribuição por Tipo de Acidente',
                     hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    # Correlação entre classificação do acidente e condições
    col1, col2 = st.columns(2)
    
    with col1:
        # Classificação dos acidentes
        class_acidentes = filtered_df['classificacao_acidente'].value_counts().reset_index()
        class_acidentes.columns = ['Classificação', 'Contagem']
        
        fig = px.pie(class_acidentes, values='Contagem', names='Classificação',
                     title='Classificação dos Acidentes')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Condições meteorológicas
        cond_meteo = filtered_df['condicao_metereologica'].value_counts().reset_index()
        cond_meteo.columns = ['Condição Meteorológica', 'Contagem']
        
        fig = px.pie(cond_meteo, values='Contagem', names='Condição Meteorológica',
                     title='Condições Meteorológicas nos Acidentes')
        st.plotly_chart(fig, use_container_width=True)
    
    # Análise cruzada: Tipo de acidente x Fase do dia
    cross_fase_tipo = pd.crosstab(filtered_df['fase_dia'], filtered_df['tipo_acidente'])
    
    # Considerando os top 5 tipos de acidentes para melhor visualização
    top5_tipos = filtered_df['tipo_acidente'].value_counts().head(5).index.tolist()
    cross_fase_tipo_filtered = cross_fase_tipo[top5_tipos]
    
    fig = px.imshow(cross_fase_tipo_filtered, 
                    labels=dict(x="Tipo de Acidente", y="Fase do Dia", color="Contagem"),
                    title="Relação entre Fase do Dia e Tipo de Acidente",
                    color_continuous_scale='Viridis')
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Perfil das Vítimas e Veículos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição por sexo
        if 'sexo' in filtered_df.columns:
            sexo_df = filtered_df['sexo'].value_counts().reset_index()
            sexo_df.columns = ['Sexo', 'Contagem']
            
            fig = px.pie(sexo_df, values='Contagem', names='Sexo',
                        title='Distribuição por Gênero')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuição por faixa etária
        if 'idade' in filtered_df.columns:
            # Criar faixas etárias
            filtered_df['faixa_etaria'] = pd.cut(
                filtered_df['idade'], 
                bins=[0, 18, 25, 35, 45, 60, 100], 
                labels=['0-18', '19-25', '26-35', '36-45', '46-60', '60+']
            )
            
            faixa_etaria_df = filtered_df['faixa_etaria'].value_counts().reset_index()
            faixa_etaria_df.columns = ['Faixa Etária', 'Contagem']
            
            fig = px.bar(faixa_etaria_df, x='Faixa Etária', y='Contagem',
                        title='Distribuição por Faixa Etária',
                        color='Contagem', color_continuous_scale='Greens')
            st.plotly_chart(fig, use_container_width=True)
    
    # Análise de veículos
    col1, col2 = st.columns(2)
    
    with col1:
        # Tipos de veículos envolvidos
        if 'tipo_veiculo' in filtered_df.columns:
            veiculos_df = filtered_df['tipo_veiculo'].value_counts().head(10).reset_index()
            veiculos_df.columns = ['Tipo de Veículo', 'Contagem']
            
            fig = px.bar(veiculos_df, x='Contagem', y='Tipo de Veículo',
                        title='Top 10 Tipos de Veículos Envolvidos',
                        color='Contagem', color_continuous_scale='Purples',
                        orientation='h')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Idade dos veículos
        if 'ano_fabricacao_veiculo' in filtered_df.columns:
            # Calcular idade do veículo
            anos_max = filtered_df['ano'].max()
            filtered_df['idade_veiculo'] = anos_max - filtered_df['ano_fabricacao_veiculo']
            
            # Remover valores negativos ou muito altos (provavelmente erros)
            idade_valida = filtered_df[(filtered_df['idade_veiculo'] >= 0) & (filtered_df['idade_veiculo'] <= 50)]
            
            # Criar faixas de idade dos veículos
            idade_valida['faixa_idade_veiculo'] = pd.cut(
                idade_valida['idade_veiculo'], 
                bins=[0, 5, 10, 15, 20, 30, 50], 
                labels=['0-5 anos', '6-10 anos', '11-15 anos', '16-20 anos', '21-30 anos', '31+ anos']
            )
            
            idade_veiculo_df = idade_valida['faixa_idade_veiculo'].value_counts().reset_index()
            idade_veiculo_df.columns = ['Idade do Veículo', 'Contagem']
            
            fig = px.bar(idade_veiculo_df, x='Idade do Veículo', y='Contagem',
                        title='Distribuição da Idade dos Veículos',
                        color='Contagem', color_continuous_scale='Purples')
            st.plotly_chart(fig, use_container_width=True)
    
    # Estado físico das vítimas
    if 'estado_fisico' in filtered_df.columns:
        estado_fisico_df = filtered_df['estado_fisico'].value_counts().reset_index()
        estado_fisico_df.columns = ['Estado Físico', 'Contagem']
        
        fig = px.pie(estado_fisico_df, values='Contagem', names='Estado Físico',
                    title='Estado Físico das Vítimas')
        st.plotly_chart(fig, use_container_width=True)

# Área para download dos dados filtrados
st.markdown("---")
st.subheader("Download dos Dados Filtrados")

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download CSV",
    data=csv,
    file_name="acidentes_filtrados.csv",
    mime="text/csv",
)

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center;">
    <p>Dashboard de Análise de Acidentes Rodoviários</p>
</div>
""", unsafe_allow_html=True)

# Instruções para execução
st.sidebar.markdown("---")
st.sidebar.subheader("Instruções de Uso")
st.sidebar.markdown("""
1. Utilize os filtros acima para refinar os dados
2. Navegue pelas abas para diferentes análises
3. Passe o mouse sobre os gráficos para detalhes
4. Baixe os dados filtrados em formato CSV
""")