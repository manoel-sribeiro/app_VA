import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt  # Importando o matplotlib para gerar as cores
import plotly.express as px
import json
import requests
from collections import defaultdict
import networkx as nx
import plotly.graph_objects as go

#Obtendo dados
df_programs = pd.read_excel('br-capes-colsucup-prog-2021-2023-11-30.xlsx')
df_programs = df_programs[df_programs['CD_CONCEITO_PROGRAMA'] == "7"]
df_docentes = pd.read_excel('br-capes-colsucup-docente-2020-2021-11-10.xlsx')
df_docentes = df_docentes[df_docentes['CD_CONCEITO_PROGRAMA'] == "7"]

# Passo 1: Criar o dataframe com estados e áreas de conhecimento
df_state_area = df_programs.groupby(['SG_UF_PROGRAMA', 'NM_GRANDE_AREA_CONHECIMENTO']).size().reset_index(name='Número de Programas')

# Passo 2: Atribuição automática de cores para as áreas de conhecimento
areas_unicas = df_programs['NM_GRANDE_AREA_CONHECIMENTO'].unique()

# Gerando uma paleta de cores automática
num_areas = len(areas_unicas)
cores_paleta = plt.cm.get_cmap('tab20', num_areas)  # Usando a paleta 'tab20' do matplotlib

# Criando um dicionário de cores associadas a cada área de conhecimento
cores_area = {area: f'rgb({int(cores_paleta(i)[0] * 255)}, {int(cores_paleta(i)[1] * 255)}, {int(cores_paleta(i)[2] * 255)})'
              for i, area in enumerate(areas_unicas)}

# Passo 3: Criar o dataframe com estados, áreas de conhecimento e cálculo da cor ponderada
# Contagem de programas por estado e área
df_state = df_state_area.pivot_table(index='SG_UF_PROGRAMA', columns='NM_GRANDE_AREA_CONHECIMENTO', values='Número de Programas', fill_value=0)

# Função para calcular a cor ponderada para cada estado
def rgb_to_list(rgb):
    rgb = rgb[4:-1]  # Remove 'rgb(' e ')'
    return list(map(int, rgb.split(',')))

# Função para converter de volta a lista (R, G, B) para a string 'rgb(R, G, B)'
def list_to_rgb(rgb_list):
    return f'rgb({rgb_list[0]}, {rgb_list[1]}, {rgb_list[2]})'

# Função para calcular a cor ponderada para cada estado
def calcular_cor_estado(row):
    cores_pesadas = []
    total_programas = row.sum()
    
    for area in df_state.columns:
        if row[area] > 0:
            # Obter a cor da área e converter para lista (R, G, B)
            cor_area = rgb_to_list(cores_area[area])
            
            # Ponderar a cor com o número de programas dessa área
            peso = row[area] / total_programas
            cor_ponderada = [int(c * peso) for c in cor_area]
            
            cores_pesadas.append(cor_ponderada)
    
    if len(cores_pesadas) == 1:
        return list_to_rgb(cores_pesadas[0])
    else:
        # Se houver várias áreas, somamos as cores ponderadas
        cor_combinada = np.mean(cores_pesadas, axis=0).astype(int)
        return (list_to_rgb(cor_combinada))

# Atribuindo cores ponderadas aos estados
df_state['Cor do Estado'] = df_state.apply(calcular_cor_estado, axis=1)
df_state.reset_index(inplace=True)
# Criar hover com informações detalhadas
df_state['hover_info'] = df_state.apply(
    lambda row: f"Estado: {row['SG_UF_PROGRAMA']}<br>" + 
                "<br>".join([f"{area}: {int(row[area])}" for area in areas_unicas if row[area] > 0]),
    axis=1
)


# Carregar o GeoJSON com todos os estados do Brasil
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
response = requests.get(geojson_url)
brazil_geojson = response.json()

# Criar uma lista com todas as unidades da federação
uf_geojson = [feature["properties"]["sigla"] for feature in brazil_geojson["features"]]
df_all_states = pd.DataFrame({'SG_UF_PROGRAMA': uf_geojson})

# Contar o número de programas por estado e área de conhecimento
df_count = df_programs.groupby(['SG_UF_PROGRAMA', 'NM_GRANDE_AREA_CONHECIMENTO']).size().reset_index(name='count')

# Detectar automaticamente as áreas de conhecimento únicas
areas_conhecimento = df_count['NM_GRANDE_AREA_CONHECIMENTO'].unique()

# Criar uma tabela pivô para contar as áreas de conhecimento por estado
df_pivot = df_count.pivot(index='SG_UF_PROGRAMA', columns='NM_GRANDE_AREA_CONHECIMENTO', values='count').fillna(0).reset_index()

# Garantir que todos os estados estejam representados
df_final = df_all_states.merge(df_pivot, on='SG_UF_PROGRAMA', how='left').fillna(0)

# Criar hover com informações detalhadas
df_final['hover_info'] = df_final.apply(
    lambda row: f"Estado: {row['SG_UF_PROGRAMA']}<br>" + 
                "<br>".join([f"{area}: {int(row[area])}" for area in areas_conhecimento if row[area] > 0]),
    axis=1
)

# Adicionar uma coluna 'soma_programas' que será usada para definir a cor
df_final['Número de Programas'] = df_final[areas_conhecimento].sum(axis=1)

# Gerar o mapa com coloração proporcional à soma dos programas
fig = px.choropleth(
    df_final,
    geojson=brazil_geojson,
    locations="SG_UF_PROGRAMA",
    featureidkey="properties.sigla",
    color='Número de Programas',  # Usar a soma dos programas como base para cor
    hover_name="SG_UF_PROGRAMA",
    hover_data={'hover_info': True, 'SG_UF_PROGRAMA': False},
    title="Distribuição dos Programas de Pós-Graduação Conceito 7 no Território Nacional",
    color_continuous_scale="turbo",  # Ajuste para a escala de cores
    range_color=[0, df_final['Número de Programas'].max()]  # Começar a escala de cores em 0.1 (evitar branco)
)

# Ajustar a escala de cores e a visualização
fig.update_geos(fitbounds="locations", visible=False)



# Menu na barra lateral
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Programas & Instituições", "Corpo Docente", "Produção Científica"])

with tab1:
    # Título da aplicação
    st.title("Programas de Pós-Graduação Conceito 7 no Brasil")

    # Texto e Widgets
    st.subheader("Este dashboard foi desenvolvido na Disciplina de Visual Analytics for Data Science")

    # Filtro das grandes áreas de conhecimento
    areas_selecionadas = st.multiselect(
        "Selecione as Grandes Áreas de Conhecimento:",
        options=areas_unicas,
        default=areas_unicas  # Pre-seleciona todas as áreas
    )

    # Filtrar os dados com base na seleção do usuário
    if areas_selecionadas:
        df_filtered = df_programs[df_programs['NM_GRANDE_AREA_CONHECIMENTO'].isin(areas_selecionadas)]
    else:
        df_filtered = df_programs  # Caso nenhuma área seja selecionada

    # Recalcular os dados com base no filtro
    df_state_filtered = df_filtered.groupby('SG_UF_PROGRAMA').size().reset_index(name='Número de Programas')

    # Atualizar o mapa
    df_state_map = df_all_states.merge(df_state_filtered, on='SG_UF_PROGRAMA', how='left').fillna(0)
    df_state_map['hover_info'] = df_state_map.apply(
        lambda row: f"Estado: {row['SG_UF_PROGRAMA']}<br>Número de Programas: {int(row['Número de Programas'])}",
        axis=1
    )

    fig_filtered = px.choropleth(
        df_state_map,
        geojson=brazil_geojson,
        locations="SG_UF_PROGRAMA",
        featureidkey="properties.sigla",
        color='Número de Programas',
        hover_name="SG_UF_PROGRAMA",
        hover_data={'hover_info': True, 'SG_UF_PROGRAMA': False},
        title="Distribuição dos Programas de Pós-Graduação Conceito 7 no Território Nacional",
        color_continuous_scale="turbo",
        range_color=[0, df_state_map['Número de Programas'].max()]
    )

    fig_filtered.update_geos(fitbounds="locations", visible=False)

    # Exibir o mapa filtrado
    st.plotly_chart(fig_filtered)

    # Tabela atualizada
    st.subheader("Ranking dos Estados por Número de Programas de Pós-Graduação Conceito 7")

    # Ordenar os dados
    df_state_sorted = df_state_map.sort_values('Número de Programas', ascending=False).rename(
        columns={'SG_UF_PROGRAMA': 'Estado'}
    )
    df_state_sorted = df_state_sorted[['Estado', 'Número de Programas']].reset_index(drop=True)
    df_state_sorted.index += 1

    # Exibir a tabela
    st.write(df_state_sorted)

    
with tab2:
    # Criar lista única de áreas de conhecimento
    unique_areas = sorted(df_programs['NM_AREA_CONHECIMENTO'].unique())
    
    st.subheader("Programas & Instituições")
    
    # Filtro de seleção única no Streamlit
    selected_area =  st.multiselect(
        "Selecione as Áreas de Conhecimento:",
        options=unique_areas,
        default=unique_areas  # Pre-seleciona todas as áreas
    )

    if selected_area:
    # Filtrar o DataFrame com base na área selecionada
        filtered_df = df_programs[df_programs['NM_AREA_CONHECIMENTO'].isin(selected_area)]
    else:
        filtered_df = df_programs

    # Agrupar os dados por Estado e Área de Conhecimento
    df_treemap = filtered_df.groupby(['SG_UF_PROGRAMA', 'NM_AREA_CONHECIMENTO']).size().reset_index(name='Número de Programas')

    # Verificar se há dados após o filtro
    if not df_treemap.empty:
        # Criar o gráfico de árvore
        fig = px.treemap(
            df_treemap,
            path=['SG_UF_PROGRAMA', 'NM_AREA_CONHECIMENTO'],  # Estrutura hierárquica: Estado > Área de Conhecimento
            values='Número de Programas',                   # Tamanho dos blocos com base no número de programas
            color='Número de Programas',                    # Coloração com base na mesma métrica
            color_continuous_scale='turbo',               # Escala de cores
            title=f"Distribuição de Programas de Pós-Graduação Conceito 7 por Estado ({selected_area})"
        )
        # Ajustar layout do gráfico
        fig.update_traces(textinfo="label+value")  # Mostra o nome e o valor em cada bloco

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig)
                
    else:
        # Exibir mensagem caso não haja dados para a seleção
        st.warning(f"Nenhum dado disponível para a área de conhecimento '{selected_area}'.")

    # Filtrar o DataFrame com base na área selecionada
    filtered_df_inst = filtered_df

    # Agrupar os dados por Instituição e Área de Conhecimento
    df_treemap_inst = filtered_df_inst.groupby(['SG_ENTIDADE_ENSINO', 'NM_AREA_CONHECIMENTO']).size().reset_index(name='Número de Programas')

    # Verificar se há dados após o filtro
    if not df_treemap_inst.empty:
        # Criar o gráfico de árvore
        fig_inst = px.treemap(
            df_treemap_inst,
            path=['SG_ENTIDADE_ENSINO', 'NM_AREA_CONHECIMENTO'],  # Estrutura hierárquica: Instituição > Área de Conhecimento
            values='Número de Programas',
            color='Número de Programas',
            color_continuous_scale='turbo',
            title=f"Distribuição de Programas por Instituição ({selected_area})"
        )
        # Exibir o gráfico
        st.plotly_chart(fig_inst)
    else:
        st.warning(f"Nenhum dado disponível para a área de conhecimento '{selected_area}'.")
    
    
    # Filtrar o DataFrame com base na área selecionada
    filtered_df_year = filtered_df
    
    # Verificar se há dados após o filtro
    if not filtered_df_year.empty:
        # Criar o histograma
        fig_hist = px.histogram(
            filtered_df_year,
            x='AN_INICIO_PROGRAMA',
            nbins=20,  # Número de bins no histograma
            title=f"Distribuição dos Anos de Início dos Programas ({selected_area})",
            labels={'AN_INICIO_PROGRAMA': 'Ano de Início'},
            color_discrete_sequence=['blue']
        )
        fig_hist.update_layout(bargap=0.2)  # Ajuste do espaçamento entre as barras

        # Exibir o histograma
        st.plotly_chart(fig_hist)
        
        # Ordenar a tabela por Ano de Início
        table_df = filtered_df_year[['NM_AREA_CONHECIMENTO', 'SG_UF_PROGRAMA', 'SG_ENTIDADE_ENSINO', 'AN_INICIO_PROGRAMA']].rename(
            columns={
                'NM_AREA_CONHECIMENTO': 'Área de Conhecimento',
                'SG_UF_PROGRAMA': 'Estado',
                'SG_ENTIDADE_ENSINO': 'Instituição',
                'AN_INICIO_PROGRAMA': 'Ano de Início'
            }
        ).sort_values(by='Ano de Início', ascending=True).reset_index(drop=True)
        table_df.index += 1
        #remover separador de milhar
        table_df['Ano de Início'] = table_df['Ano de Início'].apply(lambda x: '{:.0f}'.format(x))

        
        # Exibir a tabela
        st.write("Tabela Detalhada dos Programas")
        st.dataframe(table_df)
    else:
        st.warning(f"Nenhum dado disponível para a área de conhecimento '{selected_area}'.")
with tab3:
    st.subheader("Corpo Docente")
    # Concatenar as colunas para o título do nó
    df_docentes['NOME_NO'] = df_docentes['NM_PROGRAMA_IES'] + ' - ' + df_docentes['SG_ENTIDADE_ENSINO']

    # Seletor de programas
    search_string = st.text_input("Filtrar programas:", "")

    # Seletor de área de conhecimento (agora seletor único)
    area_selecionada = st.selectbox(
        "Selecione a área de conhecimento:",
        options=df_docentes['NM_AREA_CONHECIMENTO'].unique(),
        index=0  # Seleciona a primeira área por padrão
    )

    # Filtrar o DataFrame com base no input
    df_filtrado = df_docentes[
        df_docentes['NM_AREA_CONHECIMENTO'] == area_selecionada
    ]

    if search_string:
        # Filtra os nós com base na string de busca
        df_filtrado = df_filtrado[df_filtrado['NOME_NO'].str.contains(search_string, case=False)]

    # Criar o grafo com NetworkX
    G = nx.DiGraph()

    # Adicionar nós e arestas ao grafo
    for _, row in df_filtrado.iterrows():
        # Adicionar nó (programa e entidade de ensino)
        G.add_node(row['NOME_NO'], label=row['NOME_NO'], title=row['NM_IES_TITULACAO'])
        
        # Adicionar o nó para a instituição de ensino
        if row['NM_IES_TITULACAO'] not in G:
            G.add_node(row['NM_IES_TITULACAO'],  title=row['NM_IES_TITULACAO'])

        # Adicionar aresta (de Programa para Instituição)
        G.add_edge(row['NOME_NO'], row['NM_IES_TITULACAO'])

    # Gerar o layout do grafo
    pos = nx.spring_layout(G)  # Layout para evitar sobreposição de nós

    # Extrair coordenadas dos nós
    x_nodes = [pos[node][0] for node in G.nodes()]
    y_nodes = [pos[node][1] for node in G.nodes()]

    # Extrair informações de arestas
    edges_x = []
    edges_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edges_x.append(x0)
        edges_x.append(x1)
        edges_y.append(y0)
        edges_y.append(y1)

    # Criar o gráfico com Plotly
    edge_trace = go.Scatter(
        x=edges_x, y=edges_y,
        line=dict(width=0.5, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    node_trace = go.Scatter(
        x=x_nodes, y=y_nodes,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            colorscale='turbo',
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            )
        )
    )

    # Adicionar texto ao hover
    node_text = []
    for node in G.nodes():
        node_text.append(f"{node}: {G.nodes[node]['title']}")

    node_trace.marker.color = [len(list(G.neighbors(node))) for node in G.nodes()]
    node_trace.text = node_text

    # Criar layout do gráfico
    layout = go.Layout(
        title="Grafo de Docentes e Programas de IES",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        plot_bgcolor='white',  # Fundo branco do gráfico
    )

    # Exibir no Streamlit
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
    st.plotly_chart(fig)
    
    # Gráfico de barras e linha
    # Contabilizar a frequência de cada categoria na coluna 'CD_CAT_BOLSA_PRODUTIVIDADE'
    categoria_frequencia = df_filtrado['CD_CAT_BOLSA_PRODUTIVIDADE'].value_counts()

    # Contabilizar o número de doutores (IN_DOUTOR == 'S') em cada categoria
    doutores_frequencia = df_filtrado[df_filtrado['IN_DOUTOR'] == 'S']['CD_CAT_BOLSA_PRODUTIVIDADE'].value_counts()

    # Criar o gráfico de barras e linhas
    fig = go.Figure()

    # Adicionar a barra para a frequência das categorias
    fig.add_trace(go.Bar(
        x=categoria_frequencia.index,
        y=categoria_frequencia.values,
        name="Frequência de Categoria",
        marker=dict(color='lightblue'),
    ))

    # Adicionar a linha para a contagem de doutores
    fig.add_trace(go.Scatter(
        x=doutores_frequencia.index,
        y=doutores_frequencia.values,
        name="Contagem de Doutores",
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(color='red', size=8)
    ))

    # Ajustar o layout
    fig.update_layout(
        title="Frequência de Categorias e Contagem de Doutores",
        xaxis_title="Categoria de Bolsa de Produtividade",
        yaxis_title="Frequência",
        barmode='group',
        template="plotly_white"
    )

    # Exibir o gráfico
    st.plotly_chart(fig)

    # Tabela com as colunas solicitadas
    df_tabela = df_filtrado[['NM_DOCENTE', 'NM_PAIS_NACIONALIDADE_DOCENTE', 'DS_REGIME_TRABALHO',
                            'CD_CAT_BOLSA_PRODUTIVIDADE', 'NM_AREA_BASICA_TITULACAO', 'NM_IES_TITULACAO']]

    # Renomear as colunas
    df_tabela = df_tabela.rename(columns={
        'NM_DOCENTE': 'Docente',
        'NM_PAIS_NACIONALIDADE_DOCENTE': 'Nacionalidade',
        'DS_REGIME_TRABALHO': 'Regime de Dedicação',
        'CD_CAT_BOLSA_PRODUTIVIDADE': 'Bolsista',
        'NM_AREA_BASICA_TITULACAO': 'Área de Titulação',
        'NM_IES_TITULACAO': 'Instituição-Titulação'
    }).reset_index(drop=True)
    df_tabela.index += 1

    # Exibir a tabela no Streamlit
    st.write("Tabela de Docentes Filtrados:", df_tabela)
with tab4:
    st.subheader("Produção Científica")
    st.write("Em construção...")