import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import plotly.graph_objects as go
from scipy.spatial import ConvexHull



#Obtendo dados
@st.cache_data
def DadosProg():
    df_programs = pd.read_excel('df_programs2.xlsx')
    return df_programs
@st.cache_data
def DadosDoc():
    df_programs = pd.read_excel('df_docentes2.xlsx')
    return df_programs
@st.cache_data
def DadosPub():
    df_programs = pd.read_excel('df_proj2.xlsx')
    return df_programs




# Menu na barra lateral
tab1, tab2, tab3, tab4 = st.tabs(["Home", "Programas & Instituições", "Corpo Docente", "Produção Científica"])
# Verifica se a variável 'first_run' está no session_state

if 'first_run' not in st.session_state:
    st.session_state.first_run = True  # Define como True no primeiro carregamento
    #st.write("Este é o primeiro carregamento!")
else:
    st.session_state.first_run = False  # Se já foi carregado, define como False
    #st.write("Este não é o primeiro carregamento.")


with tab1:
    if st.session_state.get("active_tab", "Home") == "Home" or st.session_state.first_run:
        df_programs = DadosProg()
        # Título da aplicação
        st.title("Programas de Pós-Graduação Conceito 7 no Brasil")

        # Texto e Widgets
        st.subheader("Este dashboard foi desenvolvido na Disciplina de Visual Analytics for Data Science")

        # Passo 1: Criar o dataframe com estados e áreas de conhecimento
        df_state_area = df_programs.groupby(['SG_UF_PROGRAMA', 'NM_GRANDE_AREA_CONHECIMENTO']).size().reset_index(name='Número de Programas')

        # Passo 2: Atribuição automática de cores para as áreas de conhecimento
        areas_unicas = df_programs['NM_GRANDE_AREA_CONHECIMENTO'].unique()

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

        # Passo 3: Criar o dataframe com estados, áreas de conhecimento e cálculo da cor ponderada
        # Contagem de programas por estado e área
        df_state = df_state_area.pivot_table(index='SG_UF_PROGRAMA', columns='NM_GRANDE_AREA_CONHECIMENTO', values='Número de Programas', fill_value=0)

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
        df_count = df_filtered.groupby(['SG_UF_PROGRAMA', 'NM_GRANDE_AREA_CONHECIMENTO']).size().reset_index(name='count')

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
    if st.session_state.get("active_tab", "Programas & Instituições") == "Programas & Instituições" or st.session_state.first_run:
        df_programs = DadosProg()
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

                    # Criar o gráfico de árvore
            fig_are = px.treemap(
                df_treemap_inst,
                path=['NM_AREA_CONHECIMENTO', 'SG_ENTIDADE_ENSINO'],  # Estrutura hierárquica: Instituição > Área de Conhecimento
                values='Número de Programas',
                color='Número de Programas',
                color_continuous_scale='turbo',
                title=f"Distribuição de Programas por Área & Instituição ({selected_area})"
            )
            # Exibir o gráfico
            st.plotly_chart(fig_are)
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
            table_df = filtered_df_year[['NM_PROGRAMA_IES','NM_AREA_CONHECIMENTO', 'SG_UF_PROGRAMA', 'SG_ENTIDADE_ENSINO', 'AN_INICIO_PROGRAMA']].rename(
                columns={
                    'NM_PROGRAMA_IES': 'Programa',
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
    if st.session_state.get("active_tab", "Corpo Docente") == "Corpo Docente" or st.session_state.first_run:
        df_docentes = DadosDoc()
        st.subheader("Corpo Docente")
        # Concatenar as colunas para o título do nó
        df_docentes['NOME_NO'] = df_docentes['NM_PROGRAMA_IES'] + ' - ' + df_docentes['SG_ENTIDADE_ENSINO']

        # Seletor de programas
        search_string = st.text_input("Filtrar programas:", "", key="search_string")

        # Seletor de área de conhecimento (agora seletor único)
        area_selecionada = st.selectbox(
            "Selecione a área de conhecimento:",
            options=sorted(df_docentes['NM_AREA_CONHECIMENTO'].unique()),
            index=0  # Seleciona a primeira área por padrão
        )

        # Filtrar o DataFrame com base no input
        df_filtrado = df_docentes[
            df_docentes['NM_AREA_CONHECIMENTO'] == area_selecionada
        ]

        if search_string:
            # Filtra os nós com base na string de busca
            df_filtrado = df_filtrado[df_filtrado['NOME_NO'].str.contains(search_string, case=False)]

        #Agrupa as informações do df_filtrado por NOME_NO E NM_IES_TITULACAO COM FUNÇÃO DE AGREGAÇÃO SENDO A CONTAGEM DE DOCENTES
        df_filtradoG = df_filtrado.groupby(['NOME_NO', 'NM_IES_TITULACAO']).size().reset_index(name='N_DOCENTES')


        fig = px.icicle(df_filtradoG, path=[px.Constant(area_selecionada), 'NOME_NO', 'NM_IES_TITULACAO'], values='N_DOCENTES',
                        color='NOME_NO', hover_data=['N_DOCENTES'],
                        color_continuous_scale='RdBu',
                        title="Icicle Chart: Locais de Titulação por Programa")
        fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig)

        # Gráfico de barras e linha
        # Defina a ordem das categorias
        categorias_ordem = ["1A", "1B", "1C", "1D", "2", "Não Bolsista"]
        
        # Substitua os valores NaN (null) por "Não Bolsista"
        df_filtrado['CD_CAT_BOLSA_PRODUTIVIDADE'].fillna("Não Bolsista", inplace=True)

        # Converta a coluna para um tipo categórico com a ordem definida
        df_filtrado['CD_CAT_BOLSA_PRODUTIVIDADE'] = pd.Categorical(
            df_filtrado['CD_CAT_BOLSA_PRODUTIVIDADE'], categories=categorias_ordem, ordered=True
        )

        # Agora aplique o value_counts e ordene de acordo com a ordem definida
        categoria_frequencia = df_filtrado['CD_CAT_BOLSA_PRODUTIVIDADE'].value_counts().sort_index()

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

        # # Adicionar a linha para a contagem de doutores
        # fig.add_trace(go.Scatter(
        #     x=doutores_frequencia.index,
        #     y=doutores_frequencia.values,
        #     name="Contagem de Doutores",
        #     mode='lines+markers',
        #     line=dict(color='red', width=2),
        #     marker=dict(color='red', size=8)
        # ))

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
    if st.session_state.get("active_tab", "Produção Científica") == "Produção Científica"or st.session_state.first_run:
        st.subheader("Produção Científica")
        df_publis = DadosPub()
        
        # Seletor de área de conhecimento (agora seletor único)
        area_selecionada = st.selectbox(
            "Selecione a área de conhecimento:",
            options=sorted(df_publis['NM_AREA_CONHECIMENTO'].unique()),
            index=0  # Seleciona a primeira área por padrão
        )

        # Filtrar o DataFrame com base no input
        df_filtrado = df_publis[
            df_publis['NM_AREA_CONHECIMENTO'] == area_selecionada
        ]

        # Seletor de programas
        #search_string1 = st.text_input("Filtrar programas:", "", key="search_string1")
        Univ = st.multiselect(
            "Filtrar Instituições:",
            options=sorted(df_filtrado['SG_ENTIDADE_ENSINO'].unique()),
            default=sorted(df_filtrado['SG_ENTIDADE_ENSINO'].unique())  # Pre-seleciona todas as áreas
        )

        if Univ:
            # Filtra os nós com base na string de busca
            df_filtrado = df_filtrado[df_filtrado['SG_ENTIDADE_ENSINO'].isin(Univ)]

        # Contar a quantidade de publicações por PPG e ano
        df_barras = df_filtrado.groupby(['AN_BASE', 'PPG']).size().reset_index(name='Quantidade')

        # Criar gráfico de barras clusterizado
        fig_barras = px.bar(
            df_barras,
            x='AN_BASE',
            y='Quantidade',
            color='PPG',
            barmode='group',
            title='Quantidade de Publicações por PPG e Ano',
            labels={'AN_BASE': 'Ano Base', 'Quantidade': 'Quantidade de Publicações'}
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig_barras)

            # Área para o usuário indicar um parâmetro numérico
        parametro = st.number_input(
            "Número Mínimo de Publicações por Periódico:",
            min_value=0,
            max_value=100,
            value=5,  # Valor default
            step=1
        )

        st.write("Periódicos mais frequentes")
        df_agrupado = df_filtrado.groupby(['PPG', 'DS_TITULO_PADRONIZADO'])['NM_PRODUCAO'].nunique().reset_index()
        df_agrupado =df_agrupado[df_agrupado['NM_PRODUCAO'] >= parametro]

        df_agrupado['DS_TITULO_PADRONIZADO'] = df_agrupado['DS_TITULO_PADRONIZADO'].apply(lambda x: x.replace(" ", "<br>", 2))  # Exemplo de quebra após o primeiro espaço
        df_agrupado['PPG'] = df_agrupado['PPG'].apply(lambda x: x.replace("-", "<br>", 1))  # Exemplo de quebra
        # Criando o gráfico Sunburst
        figsun =  px.sunburst(df_agrupado, path=['PPG', 'DS_TITULO_PADRONIZADO'], values='NM_PRODUCAO', color='PPG')  # A cor pode ser personalizada por qualquer coluna
        #figsun.update_layout(uniformtext=dict(minsize=10, mode='hide'))

        # Exibindo o gráfico no Streamlit
        st.plotly_chart(figsun)
        # Gera uma paleta com cores distintas para cada título
        unique_titles = df_agrupado['DS_TITULO_PADRONIZADO'].unique()
        num_titles = len(unique_titles)
        palette = px.colors.qualitative.Set3 * (num_titles // len(px.colors.qualitative.Set3) + 1)  # Multiplica paleta se necessário

        figsun2 = px.sunburst(
            df_agrupado,
            path=['DS_TITULO_PADRONIZADO', 'PPG'],
            values='NM_PRODUCAO',
            color='DS_TITULO_PADRONIZADO',
            color_discrete_sequence=palette[:num_titles]  # Usa cores suficientes
        )  # A cor pode ser personalizada por qualquer coluna
        #figsun2.update_layout(uniformtext=dict(minsize=10, mode='hide'))
        # Exibindo o gráfico no Streamlit
        st.plotly_chart(figsun2)

        st.write("Comparativo de Publicações por PPG")
        anos = df_filtrado['AN_BASE'].unique()
        # Adicionando o seletor de anos
        # Usando o select_slider para permitir a seleção de um intervalo de anos
        ano_inicial, ano_final = st.select_slider(
            'Selecione o período de anos:',
            options=anos,
            value= (df_filtrado['AN_BASE'].min(), df_filtrado['AN_BASE'].max())  # Valor inicial do intervalo (ano de início e fim)
        )

        df_refiltrado = df_filtrado[df_filtrado['AN_BASE'] >= ano_inicial]
        
                # Criação de um seletor binário usando radio buttons
        #opcao = st.radio('Escolha uma opção:', ('Kmeans', 'DBSCAN'))

        # Mostrar a opção escolhida
        #if opcao == 'Kmeans':
        k = st.selectbox(
        'Escolha o número de clusters:',
        [3, 5, 7, 9, 11, 13, 15, 17],  # Número de clusters,
        index=3  # Índice de 9 na lista (começa em 0)
        )
        
        if k == 3:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_3']
        elif k == 5:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_5']
        elif k == 7:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_7']
        elif k == 9:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_9']
        elif k == 11:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_11']
        elif k == 13:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_13']
        elif k == 15:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_15']
        elif k == 17:
            df_refiltrado['cluster'] = df_refiltrado['Cluster_17']
        # else:
        #     df_refiltrado['cluster'] = df_refiltrado['Cluster_DBSCAN']
        #     k = len(df_refiltrado['cluster'].unique())
        
        id_cluster = df_refiltrado['cluster'].unique()
        #Ordenar os clusters
        id_cluster = np.sort(id_cluster)
        #Adicionar 1 em cada id_cluster
        id_cluster = id_cluster + 1
           
        # Filtro das grandes áreas de conhecimento
        clusters_selecionados = st.multiselect(
            "Selecione os clústers visíveis:",
            options=id_cluster,
            default=id_cluster  # Pre-seleciona todas as áreas
        )
        
        #remove 1 de cada cluster selecionado
        clusters_selecionados = [x - 1 for x in clusters_selecionados]
        
        # Filtrar os dados com base na seleção do usuário
        if clusters_selecionados:
            df_refiltrado = df_refiltrado[df_refiltrado['cluster'].isin(clusters_selecionados)]
        else:
            df_refiltrado = df_refiltrado
            
        # 2. Visualização no plano 2D
        fig = px.scatter(
            df_refiltrado,
            x="Dimensão 1",
            y="Dimensão 2",
            color="PPG",  # Coloração baseada em `PPG`
            title="Projeção 2D das Publicações com Clusters",
            #text="cluster",
            hover_data=["NM_PRODUCAO", "cluster"],  # Informações extras no hover
            labels={"PPG": "Programa", "x": "Dimensão 1", "y": "Dimensão 2"}
        )

        # 3. Adicionar figuras geométricas para os clusters
        for cluster_id in range(k):
            # Filtrar os pontos do cluster atual
            cluster_points = df_refiltrado[df_refiltrado['cluster'] == cluster_id][["Dimensão 1", "Dimensão 2"]].values

            if len(cluster_points) >= 3:  # ConvexHull exige pelo menos 3 pontos
                hull = ConvexHull(cluster_points)
                hull_points = cluster_points[hull.vertices]
                hull_points = np.append(hull_points, [hull_points[0]], axis=0)  # Fechar o polígono
                
                # Adicionar o polígono ao gráfico
                fig.add_trace(
                go.Scatter(
                    x=hull_points[:, 0],
                    y=hull_points[:, 1],
                    fill='toself',
                    mode='lines',
                    line_color='rgba(64, 64, 64, 0.7)',  # Borda branca semi-transparente
                    name=f"Cluster {cluster_id + 1}",
                    text=f"Cluster {cluster_id + 1}",
                    opacity=0.3,  # Transparência no preenchimento
                    hoverinfo='skip'  # Desativa o hover para o polígono
                )
                )

        # Ajustar layout para melhor visualização
        fig.update_traces(textposition="top center")
        fig.update_layout(
            title_font_size=18,
            xaxis_title="Dimensão 1",
            yaxis_title="Dimensão 2",
            template="plotly_white",
            showlegend=True
        )

        # Exibir o gráfico
        st.plotly_chart(fig)

        table_df = df_refiltrado[["NM_PRODUCAO", "PPG", "cluster"]].rename(
            columns={
                "NM_PRODUCAO": "Título",
                "PPG": "Programa",
                "cluster": "Cluster"
            }
        ).sort_values(by="Cluster", ascending=True).reset_index(drop=True)
        # Exibir a tabela
        table_df['Cluster'] = table_df['Cluster'] + 1
        st.write("Publicações Filtradas:")
        st.dataframe(table_df)
