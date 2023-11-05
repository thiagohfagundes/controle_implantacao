import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from functions import atualiza_dados, metricas_em_andamento, metricas_dashboard, ultimos12meses, tabelatempos
import plotly.express as px
from pandas._libs.tslibs.timestamps import Timestamp

st.set_page_config(
    page_title='Controle Implantação 🚀', 
    page_icon='🚀', 
    layout="wide", 
    #initial_sidebar_state="auto", 
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

implantacoes, em_andamento, data_atualizacao = atualiza_dados()
colunastempos_ms = [item for item in implantacoes.columns if 'time' in item]
implantacoes_sem_tempos = implantacoes.drop(columns = colunastempos_ms).round(2)
em_andamento_sem_tempos = em_andamento.drop(columns = colunastempos_ms).round(2)
lista_colunas = implantacoes_sem_tempos.columns.to_list()
lista_proprietarios = implantacoes_sem_tempos['Nome do proprietário'].unique()

# ----------- Sidebar ------------ #
with st.sidebar:
    datacriacao = st.date_input(
        "Filtre por data de criação",
        (implantacoes_sem_tempos['createdate'].min(), implantacoes_sem_tempos['createdate'].max()),
        format="DD/MM/YYYY",
    )

    datafinalizacao = st.date_input(
        "Filtre por data de fechamento",
        (implantacoes_sem_tempos['closed_date'].min(), implantacoes_sem_tempos['closed_date'].max()),
        format="DD/MM/YYYY",
    )

    proprietarios = st.multiselect(
        'Filtre por proprietário',
        lista_proprietarios,
    )

    extras = st.toggle("Implantações e treinamentos extras")

    aplicar = st.button("Aplicar filtros")
    resetar = st.button("Resetar filtros")

    # Funcionamento dos filtros
    if aplicar:
        datainiciocriacao = Timestamp(datacriacao[0], tz='UTC')
        datafinalcriacao = Timestamp(datacriacao[1], tz='UTC')
        datainiciofechamento = Timestamp(datafinalizacao[0], tz='UTC')
        datafinalfechamento = Timestamp(datafinalizacao[1], tz='UTC')
        implantacoes_sem_tempos = implantacoes_sem_tempos.loc[(implantacoes_sem_tempos['implantacao_extra']==extras)&(implantacoes_sem_tempos['createdate']>=datainiciocriacao)&(implantacoes_sem_tempos['createdate']<=datafinalcriacao)&(implantacoes_sem_tempos['closed_date']>=datainiciofechamento)&(implantacoes_sem_tempos['closed_date']<=datafinalfechamento)]
        implantacoes = implantacoes.loc[(implantacoes['implantacao_extra']==extras)&(implantacoes['createdate']>=datainiciocriacao)&(implantacoes_sem_tempos['createdate']<datafinalcriacao)&(implantacoes['closed_date']>=datainiciofechamento)&(implantacoes['closed_date']<=datafinalfechamento)]       
        implantacoes_sem_tempos = implantacoes_sem_tempos.loc[implantacoes_sem_tempos["Nome do proprietário"].isin(proprietarios)]
        implantacoes = implantacoes.loc[implantacoes["Nome do proprietário"].isin(proprietarios)]
    if resetar:
        st.rerun()

# ----------- Principal ------------ #
st.write("## Controle Implantação ERP 🚀")
col1, col2 = st.columns(spec=[8,2])

with col1:
    st.write(f"Data da última atualização nos dados: {data_atualizacao.strftime('%Y-%m-%d %H:%M')}")
with col2:
    st.button("Atualizar", st.cache_data.clear())

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Dashboard", "Clientes em andamento", "Tempos", "Dados gerais", "Kickoff", "Clientes em risco", "Tarefas"])

with tab4:
    options = st.multiselect(
        'Selecione colunas a exibir',
        lista_colunas,
        lista_colunas
    )

    st.data_editor(
        implantacoes_sem_tempos,
        column_config={
            "createdate": st.column_config.DateColumn(
                "Data de criação",
                format="DD/MM/YYYY",
            ),
            "closed_date": st.column_config.DateColumn(
                "Data de fechamento",
                format="DD/MM/YYYY",
            ),
            "hs_lastmodifieddate": st.column_config.DateColumn(
                "Data da última modificação",
                format="DD/MM/YYYY",
            ),
            "cs__licenca": st.column_config.TextColumn(
                "Licença",
            ),
            "subject": st.column_config.TextColumn(
                "Nome do ticket",
            ),

        },
        hide_index=True,   
    )

with tab1:
    tempo_medio, contratos_iniciados, contratos_finalizados, contratos_cancelados, media_contratos, contagem, contratos, finalizadas_por_consultor, conversao_processo, consultores_ativos, clientes_na_fila, iniciadas_no_mes, finalizadas_no_mes, canceladas_no_mes, troughput, saldo_do_mes = metricas_dashboard(implantacoes_sem_tempos)

    st.write("#### Visão geral")

    col1, col2, col3, col4 = st.columns(spec=[1,1,1,1])
    with col1:
        st.metric("Em andamento", contagem, int(iniciadas_no_mes - finalizadas_no_mes))
        st.metric("Iniciadas no mês", int(iniciadas_no_mes))
        st.metric("Contratos finalizados", int(contratos_finalizados))
        st.metric("Finalizadas por consultor", finalizadas_por_consultor)
    with col2:
        st.metric("Tempo médio (em andamento)", tempo_medio)
        st.metric("Finalizadas no mês", int(finalizadas_no_mes))
        st.metric("Contratos iniciados", int(contratos_iniciados))
        st.metric("Conversão no processo", f"{conversao_processo}%")
    with col3:
        st.metric("Contratos em andamento", int(contratos), int(contratos_iniciados - contratos_finalizados - contratos_cancelados))
        st.metric("Canceladas no mês", int(canceladas_no_mes))
        st.metric("Contratos cancelados", int(contratos_cancelados))
        st.metric("Clientes na fila", int(clientes_na_fila))
    with col4:
        st.metric("Saldo do mês", int(saldo_do_mes))
        st.metric("Churn rate", f"{canceladas_no_mes/(contagem + finalizadas_no_mes + canceladas_no_mes)}%")
        st.metric("Consultores ativos", consultores_ativos)
        st.metric("Troughput", f"{troughput}%")

    st.divider()

    st.write("#### Entradas e saídas")
    dados_agrupados_iniciadas, dados_agrupados_finalizadas, dados_agrupados_canceladas = ultimos12meses(implantacoes_sem_tempos)

    col1, col2 = st.columns(spec=[1,1])

    with col1:
        fig = px.bar(
            dados_agrupados_iniciadas,
            x = 'mês',
            y = 'Iniciadas',
            text_auto=True,
            title='Iniciadas por mês (este ano)'
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        fig = px.bar(
            dados_agrupados_canceladas,
            x = 'mês',
            y = 'Canceladas',
            text_auto=True,
            title='Canceladas por mês (este ano)'
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    
    with col2:
        fig = px.bar(
            dados_agrupados_finalizadas,
            x = 'mês',
            y = 'Finalizadas',
            text_auto=True,
            title='Finalizadas por mês (este ano)'
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

with tab2:
    contagem, clientes_por_etapa, clientes_por_proprietario, clientes_por_plano, contratos, tempo_medio = metricas_em_andamento(em_andamento_sem_tempos)
    atrasados = em_andamento_sem_tempos.loc[em_andamento_sem_tempos['Atraso']==True].createdate.count()
    percentual_atraso = round(atrasados*100 / contagem, 2)
    col1, col2 = st.columns(spec=[1,3])
    with col1:
        st.write("#### Estatísticas")
        st.metric("Em andamento", contagem)
        st.metric("Contratos em andamento", contratos)
        st.metric("Tempo médio no processo", tempo_medio)
        st.metric("Atrasados", atrasados)
        st.metric("Perc. em atraso", f"{percentual_atraso}%")
    with col2:
        fig = px.bar(
            clientes_por_etapa,
            y='createdate',
            text_auto=True
        )
        fig.update_layout(
            title_text='Clientes por etapa',
            xaxis_title_text='Etapa', 
            yaxis_title_text='Clientes', 
            bargap=0.2, 
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    st.divider()
    st.write("#### Histogramas")
    col1, col2 = st.columns(spec=[1,1])
    with col1:
        fig = px.histogram(
            em_andamento_sem_tempos,
            x='tempo_processo', 
            nbins=30,
            text_auto=True
        )
        
        fig.update_layout(
            title_text='Histograma de tempo no processo',
            xaxis_title_text='Tempo (dias)', 
            yaxis_title_text='Clientes', 
            bargap=0.2, 
        )
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with col2:
        fig = px.histogram(
            em_andamento_sem_tempos,
            x='qtde_contratos', 
            nbins=30,
            text_auto=True
        )
        
        fig.update_layout(
            title_text='Distribuição de contratos em andamento',
            xaxis_title_text='Contratos', 
            yaxis_title_text='Clientes', 
            bargap=0.2, 
        )

        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    st.divider()

    st.write("#### Divisões")
    col1, col2 = st.columns(spec=[1,1])
    with col1:
        fig = px.pie(clientes_por_plano, values='createdate', names=clientes_por_plano.index, title='Clientes em andamento por plano')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with col2:
        fig = px.pie(clientes_por_proprietario, values='createdate', names=clientes_por_proprietario.index, title='Clientes em andamento por plano')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)

    col1, col2, col3 = st.columns(spec=[1,1,1])

    with col1:
        st.data_editor(
            clientes_por_etapa,
            column_config={
                "createdate": st.column_config.ProgressColumn(
                    "Clientes",
                    format="%f",
                    max_value=40,
                ),
            }
        )

    with col2:
        st.data_editor(
            clientes_por_proprietario,
            column_config={
                "createdate": st.column_config.ProgressColumn(
                    "Clientes",
                    format="%f",
                    max_value=20,
                ),
            }
        )

    with col3:
        st.data_editor(
            clientes_por_plano,
            column_config={
                "createdate": st.column_config.ProgressColumn(
                    "Clientes",
                    format="%f"
                ),
            }
        )

    st.divider()

    st.write("#### Todas as implantações em andamento")
    tempos = st.slider(label='Tempo no processo', value=[0, em_andamento['tempo_processo'].max()])
    extras = st.toggle("Atrasadas", value=True)

    if tempos:
        if extras == True:
            em_andamento_sem_tempos = em_andamento_sem_tempos.loc[(em_andamento_sem_tempos['Atraso']==True)&(em_andamento_sem_tempos['tempo_processo']>=tempos[0])&(em_andamento['tempo_processo']<tempos[1])]
            st.write(f"Exibindo {em_andamento_sem_tempos.createdate.count()} clientes")
            st.dataframe(em_andamento_sem_tempos)
        else:
            em_andamento_sem_tempos = em_andamento_sem_tempos.loc[(em_andamento_sem_tempos['tempo_processo']>=tempos[0])&(em_andamento_sem_tempos['tempo_processo']<tempos[1])]
            st.write(f"Exibindo {em_andamento_sem_tempos.createdate.count()} clientes")
            st.dataframe(em_andamento_sem_tempos)

with tab3:
    resumo_tempos, tabela_tempos = tabelatempos(implantacoes)
    st.write("#### Tempos por etapa")
    extras = st.toggle("Mostrar apenas clientes em andamento", value=False)

    if extras == True:
        resumo_tempos, tabela_tempos = tabelatempos(em_andamento)
        fig2 = px.scatter(
            em_andamento_sem_tempos,
            x='tempo_processo',
            y='qtde_contratos'
        )
    else:
        resumo_tempos, tabela_tempos = tabelatempos(implantacoes)
        fig2 = px.scatter(
            implantacoes_sem_tempos,
            x='tempo_processo',
            y='qtde_contratos'
        )

    fig = px.box(
        tabela_tempos,
    )

    st.plotly_chart(fig, use_container_width=True, theme='streamlit')

    st.divider()
    st.write("#### Visão geral de tempos")
    st.dataframe(resumo_tempos)

    st.write("#### Tempo x Quantidade de contratos")
    st.plotly_chart(fig2, use_container_width=True, theme='streamlit')


with tab5:
    st.write("#### Gestão de kickoff")
    st.text("Em breve")

with tab6:
    st.write("#### Clientes em risco")
    st.text("Em breve")

with tab7:
    st.write("#### Tarefas")
    st.text("Em breve")