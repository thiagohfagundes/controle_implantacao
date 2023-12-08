import streamlit as st
import pytimetk as tk
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime
from pandas._libs.tslibs.timestamps import Timestamp

access_token = st.secrets["access_token"]
app_token_assinas = st.secrets["app_token_assinas"]
access_token_assinas = st.secrets["access_token_assinas"]
object_type = 'tickets'
pipeline_id = '27860857'
propriedades = ['createdate', 'subject', 'cs__licenca', 'hs_pipeline_stage', 'hubspot_owner_id', 'imob__tiers', 'imp___erp__produto', 'imp___erp__combo', 'imob__quantidade_contratos','imob__plano_imobiliarias', 'closed_date', 'hs_date_exited_66260749']
headers_assinas = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'app_token': app_token_assinas,
    'access_token': access_token_assinas
  }


def atribuir_plano(nome_plano):
  if nome_plano != None:
    nome_plano = nome_plano.lower()
    if 'enterprise' in nome_plano:
      return 'Enterprise'
    elif 'basic' in nome_plano:
      return 'Basic'
    elif 'econômico' in nome_plano:
      return 'Econômico'
    elif 'essencial' in nome_plano:
      return 'Essencial'
    elif 'faciloca' in nome_plano:
      return 'Faciloca'
    elif 'uno' in nome_plano:
      return 'Uno'
    elif 'plano 50' in nome_plano:
      return 'Plano 50'
    else:
      return 'Sem informação'
  else:
    return 'Sem informação'

def tempoprocesso(row):
  data_inicio = row['createdate'].tz_localize(None)
  if (row['etapa_pipeline'] == 'FINALIZADAS') or (row['etapa_pipeline'] == 'CANCELADAS'):
    data_finalizada = row['closed_date'].tz_localize(None)
    diferenca = (data_finalizada - data_inicio).days
  else:
    data_hoje = datetime.now()
    diferenca = (data_hoje - data_inicio).days
  return diferenca

def tempo_na_etapa(row):
  etapa = row['hs_pipeline_stage']
  data_hoje = datetime.now()
  data_entrada_etapa = row[f"hs_date_entered_{etapa}"].tz_localize(None)
  if (etapa != '63284075') and (etapa != '63284077'):
    tempo_na_etapa = (data_hoje - data_entrada_etapa).days
    return tempo_na_etapa
  
def tempo_sem_modificacao(data):
  data_ult_modif = data.tz_localize(None)
  data_hoje = datetime.now()
  tempo_sem_modif = (data_hoje - data_ult_modif).days
  return tempo_sem_modif

def combo(status_combo):
  if status_combo == 'true':
    return True
  else:
    return False

def kenlo(licenca):
  if licenca:
    if 'adm' in licenca:
      return True
    else:
      return False
  else:
    return True

def pjbank(produtos):
  if produtos:
    if 'Boleto' in produtos or 'Bundles' in produtos:
      return True
    else:
      return False
  else:
    return False

def imp_extra(nome):
  if nome:
    nome = nome.lower()
    if 'extra' in nome:
      return True
    else:
      return False
  else:
    return True
  
def atribuir_prazo(nome_plano):
  nome_plano = nome_plano.lower()
  if (nome_plano == 'basic') | (nome_plano == 'econômico'):
    return 45
  elif nome_plano == 'essencial':
    return 60
  elif nome_plano == 'enterprise':
    return 90
  elif (nome_plano == 'faciloca') | (nome_plano == 'uno'):
    return 45
  else:
    return 45

def quantidade_contratos(qtd):
  if qtd:
    if qtd.isnumeric():
      return float(qtd)
    else:
      return np.nan

def linkhubspot(id):
  return f"https://app.hubspot.com/contacts/20131994/record/0-5/{id}"

@st.cache_data
def atualiza_dados():
    url = f"https://api.hubapi.com/crm/v3/objects/{object_type}/search"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    def conectaAPI(after):
        data = {
            "limit": 100,
            "after": after,
            "properties": propriedades,
            "filterGroups": [
                {
                    "filters": [
                        {
                        "propertyName": "hs_pipeline",
                        "operator": "EQ",
                        "value": pipeline_id
                        }
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()

    try:
        response = conectaAPI(None)
        resultados = response['results']
        total = response['total']
        df = pd.DataFrame(resultados)
        implantacoes = pd.DataFrame(df['properties'].tolist())
        paginas = round(total/100 + 1, 2)
    except Exception as e:
        print(e)

    for pagina in range(1, int(paginas)):
        after = pagina*100

        response2 = conectaAPI(after)

        resultados2 = response2['results']
        df2 = pd.DataFrame(resultados2)
        implantacoes2 = pd.DataFrame(df2['properties'].tolist())
        implantacoes = pd.concat([implantacoes, implantacoes2])

    url = f'https://api.hubapi.com/crm/v3/pipelines/{object_type}/{pipeline_id}/stages'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    stages = response.json()['results']

    stages = pd.DataFrame(stages)
    stages = stages.loc[:,['id', 'label']]
    stages.columns = ['hs_pipeline_stage', 'etapa_pipeline']

    url = "https://api.hubapi.com/owners/v2/owners"

    params = {
        "limit": 100
    }

    response = requests.get(url, headers=headers, params=params)
    df = pd.DataFrame(response.json())

    owners = df.loc[:,['ownerId',	'email', 'firstName', 'lastName']]
    owners['nome'] = owners['firstName'] + ' ' + owners['lastName']
    owners = owners.drop(columns=['firstName', 'lastName'])
    owners.columns = ['hubspot_owner_id', 'Email do proprietario', 'Nome do proprietário']

    implantacoes = pd.merge(implantacoes, stages, how='left', on='hs_pipeline_stage')
    owners['hubspot_owner_id'] = owners['hubspot_owner_id'].astype(str)
    implantacoes = pd.merge(implantacoes, owners, how='left', on='hubspot_owner_id')
    lista_colunas = implantacoes.columns.to_list()
    colunasdatas = [item for item in lista_colunas if 'date' in item]
    implantacoes[colunasdatas] = implantacoes[colunasdatas].apply(pd.to_datetime, format='ISO8601')

    implantacoes['plano_macro'] = implantacoes['imob__plano_imobiliarias'].apply(atribuir_plano)
    implantacoes['combo'] = implantacoes['imp___erp__combo'].apply(combo)
    implantacoes['kenlo'] = implantacoes['cs__licenca'].apply(kenlo)
    implantacoes['pjbank'] = implantacoes['imp___erp__produto'].apply(pjbank)
    implantacoes['qtde_contratos'] = implantacoes['imob__quantidade_contratos'].apply(quantidade_contratos)
    implantacoes['implantacao_extra'] = implantacoes['subject'].apply(imp_extra)
    implantacoes['tempo_processo'] = implantacoes.apply(tempoprocesso, axis=1)
    implantacoes['tempo_na_etapa'] = implantacoes.apply(tempo_na_etapa, axis=1)
    implantacoes['tempo_sem_modif'] = implantacoes['hs_lastmodifieddate'].apply(tempo_sem_modificacao)
    colunastempos_ms = [item for item in lista_colunas if 'time' in item]
    implantacoes[colunastempos_ms] = implantacoes[colunastempos_ms].apply(pd.to_numeric) / 86400000
    implantacoes['prazo_implantacao'] = implantacoes['plano_macro'].apply(atribuir_prazo)
    implantacoes['Atraso'] = np.where(implantacoes['tempo_processo']>implantacoes['prazo_implantacao'], True, False)
    implantacoes['Finalizadas'] = np.where(implantacoes['etapa_pipeline']=='FINALIZADAS', True, False)
    implantacoes['Canceladas'] = np.where(implantacoes['etapa_pipeline']=='CANCELADAS', True, False)
    implantacoes['Link'] = implantacoes['hs_object_id'].apply(linkhubspot)

    datas_padrao = [item for item in lista_colunas if 'hs_date' in item]
    datas = implantacoes[datas_padrao]
    colunas_inuteis = ['imob__quantidade_contratos','hubspot_owner_id', 'hs_pipeline_stage', 'imob__plano_imobiliarias', 'hs_time_in_63284077', 'hs_time_in_13217152', 'hs_time_in_13217153', 'hs_time_in_88963628']
    colunas_inuteis.extend(datas_padrao)
    implantacoes = implantacoes.drop(columns = colunas_inuteis).round(2)

    concluidas = implantacoes.loc[(implantacoes['Finalizadas']==True)|(implantacoes['Canceladas']==True)]
    em_andamento = implantacoes.loc[(implantacoes['Finalizadas']==False)&(implantacoes['Canceladas']==False)]
    em_andamento = em_andamento.drop(columns = ['closed_date', 'Finalizadas', 'Canceladas'])

    data_atualizacao = datetime.now()
    return implantacoes, em_andamento, data_atualizacao, datas, concluidas, stages

def dados_sankey(concluidas):
    tier_a = concluidas.loc[concluidas['qtde_contratos']>=1000]
    tier_b = concluidas.loc[(concluidas['qtde_contratos']>=500)&(concluidas['qtde_contratos']<1000)]
    tier_c = concluidas.loc[(concluidas['qtde_contratos']>100)&(concluidas['qtde_contratos']<500)]
    tier_d = concluidas.loc[(concluidas['qtde_contratos']>=50)&(concluidas['qtde_contratos']<100)]
    tier_e = concluidas.loc[(concluidas['qtde_contratos']<50)]
    
    iniciados = []
    finalizados = []
    cancelados = []
    for _set in (tier_a, tier_b, tier_c, tier_d, tier_e):
      iniciados.append(_set.createdate.count())
      finalizados.append(_set.loc[_set['Finalizadas']==True].createdate.count())
      cancelados.append(_set.loc[_set['Canceladas']==True].createdate.count())

    label = ['Tier A', 'Tier B', 'Tier C', 'Tier D', 'Tier E', 'Finalizadas', 'Canceladas']
    source = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    target = [5, 6, 5, 6, 5, 6, 5, 6, 5, 6]
    value = [finalizados[0], cancelados[0], finalizados[1], cancelados[1], finalizados[2], cancelados[2], finalizados[3], cancelados[3], finalizados[4], cancelados[4]]

    return label, source, target, value

def cohort_por_etapa(implantacoes):
    data_atual = datetime.now()
    datainicio = datetime(data_atual.year, 1, 1)
    datainicio = Timestamp(datainicio, tz='UTC')

    def data_cancelamento(row):
      if row['etapa_pipeline'] == 'CANCELADAS':
        return row['closed_date']
      
    implantacoes = implantacoes.loc[implantacoes['createdate']>=datainicio]

    implantacoes['data_cancelamento'] = implantacoes.apply(data_cancelamento, axis=1)
    dados_cohort = implantacoes[['createdate', 'data_cancelamento']]
    dados_cohort['mes_criacao'] = dados_cohort['createdate'].dt.month
    dados_cohort['mes_cancelamento'] = dados_cohort['data_cancelamento'].dt.month
    dados_pivot = dados_cohort.groupby(['mes_criacao', 'mes_cancelamento']).count().reset_index()
    dados_pivot = dados_pivot.pivot(index='mes_criacao', columns='mes_cancelamento', values='createdate')
    dados_pivot.fillna(0, inplace=True)

    implantacoes = implantacoes[['createdate', 'etapa_pipeline']]
    implantacoes['mes'] = implantacoes['createdate'].dt.month
    implantacoes_iniciadas = implantacoes.groupby(['mes']).count()
    implantacoes_cohort = implantacoes.groupby(['mes', 'etapa_pipeline']).count().reset_index()
    implantacoes_cohort = implantacoes_cohort.pivot(index='mes', columns='etapa_pipeline', values='createdate')
    implantacoes_cohort['INICIADAS'] = implantacoes_iniciadas[['createdate']]
    if 'CANCELADAS' in implantacoes_cohort.columns:
      implantacoes_cohort['conversão'] = round(implantacoes_cohort['FINALIZADAS']*100 / implantacoes_cohort['INICIADAS'],2)
      implantacoes_cohort['churn rate'] = round(implantacoes_cohort['CANCELADAS']*100 / implantacoes_cohort['INICIADAS'],2)
    else:
      implantacoes_cohort['conversão'] = 0
      implantacoes_cohort['churn rate'] = 0
    implantacoes_cohort.fillna(0, inplace=True)

    return implantacoes_cohort, dados_pivot

def metricas_em_andamento(implantacoes):
    contagem = implantacoes['createdate'].count()
    clientes_por_etapa = implantacoes.groupby(by='etapa_pipeline').createdate.count()
    clientes_por_proprietario = implantacoes.groupby(by='Nome do proprietário').createdate.count()
    clientes_por_plano = implantacoes.groupby(by='plano_macro').createdate.count()
    contratos = round(implantacoes['qtde_contratos'].sum())
    tempo_medio = round(implantacoes['tempo_processo'].mean(), 2)
    return contagem, clientes_por_etapa, clientes_por_proprietario, clientes_por_plano, contratos, tempo_medio

def metricas_dashboard(implantacoes):
    em_andamento = implantacoes.loc[(implantacoes['Finalizadas']==False)&(implantacoes['Canceladas']==False)]
    contagem = em_andamento['createdate'].count()
    contratos = round(em_andamento['qtde_contratos'].sum())
    consultores_ativos = em_andamento['Nome do proprietário'].nunique()
    clientes_na_fila = em_andamento.loc[em_andamento['etapa_pipeline']=='KICKOFF'].createdate.count()

    data_atual = datetime.now()
    if data_atual.month == 12:
      primeiro_dia_proximo_mes = datetime(data_atual.year, 1, 1)
    else:
      primeiro_dia_proximo_mes = datetime(data_atual.year, (data_atual.month + 1), 1)
    
    primeiro_dia_do_mes_atual = datetime(data_atual.year, data_atual.month, 1)
    primeiro_dia_do_mes_atual = Timestamp(primeiro_dia_do_mes_atual, tz='UTC')
    primeiro_dia_proximo_mes = Timestamp(primeiro_dia_proximo_mes, tz='UTC')

    iniciadas_no_mes = em_andamento.loc[(em_andamento['createdate']>=primeiro_dia_do_mes_atual)&(em_andamento['createdate']<primeiro_dia_proximo_mes)].createdate.count()
    contratos_iniciados = em_andamento.loc[(em_andamento['createdate']>=primeiro_dia_do_mes_atual)&(em_andamento['createdate']<primeiro_dia_proximo_mes)].qtde_contratos.sum()
    finalizadas_no_mes = implantacoes.loc[(implantacoes['closed_date']>=primeiro_dia_do_mes_atual)&(implantacoes['closed_date']<primeiro_dia_proximo_mes)&(implantacoes['etapa_pipeline']=='FINALIZADAS')].createdate.count()
    contratos_finalizados = implantacoes.loc[(implantacoes['closed_date']>=primeiro_dia_do_mes_atual)&(implantacoes['closed_date']<primeiro_dia_proximo_mes)&(implantacoes['etapa_pipeline']=='FINALIZADAS')].qtde_contratos.sum()
    canceladas_no_mes = implantacoes.loc[(implantacoes['closed_date']>=primeiro_dia_do_mes_atual)&(implantacoes['closed_date']<primeiro_dia_proximo_mes)&(implantacoes['etapa_pipeline']=='CANCELADAS')].createdate.count()
    contratos_cancelados = implantacoes.loc[(implantacoes['closed_date']>=primeiro_dia_do_mes_atual)&(implantacoes['closed_date']<primeiro_dia_proximo_mes)&(implantacoes['etapa_pipeline']=='CANCELADAS')].qtde_contratos.sum()
    media_contratos = em_andamento.qtde_contratos.mean()
    saldo_do_mes = iniciadas_no_mes - finalizadas_no_mes - canceladas_no_mes
    finalizadas_por_consultor = round(finalizadas_no_mes / consultores_ativos, 2)
    conversao_processo = round(finalizadas_no_mes*100 / (contagem + finalizadas_no_mes + canceladas_no_mes),2)
    troughput = round(finalizadas_no_mes / iniciadas_no_mes, 2)
    tempo_medio = round(em_andamento['tempo_processo'].mean(), 2)

    return tempo_medio, contratos_iniciados, contratos_finalizados, contratos_cancelados, media_contratos, contagem, contratos, finalizadas_por_consultor, conversao_processo, consultores_ativos, clientes_na_fila, iniciadas_no_mes, finalizadas_no_mes, canceladas_no_mes, troughput, saldo_do_mes

def ultimos12meses(implantacoes):
    data_atual = datetime.now()
    inicio = datetime(data_atual.year, 1, 1)
    inicio = Timestamp(inicio, tz='UTC')
    data_atual = Timestamp(data_atual, tz='UTC')

    iniciadas = implantacoes.loc[(implantacoes['createdate']>=inicio)&(implantacoes['createdate']<data_atual)]
    iniciadas['mês'] = iniciadas['createdate'].dt.month
    dados_agrupados_iniciadas = iniciadas.groupby('mês').size().reset_index(name='Iniciadas')

    finalizadas = implantacoes.loc[(implantacoes['closed_date']>=inicio)&(implantacoes['closed_date']<data_atual)&(implantacoes['etapa_pipeline']=='FINALIZADAS')]
    finalizadas['mês'] = finalizadas['closed_date'].dt.month
    dados_agrupados_finalizadas = finalizadas.groupby('mês').size().reset_index(name='Finalizadas')

    canceladas = implantacoes.loc[(implantacoes['closed_date']>=inicio)&(implantacoes['closed_date']<data_atual)&(implantacoes['etapa_pipeline']=='CANCELADAS')]
    canceladas['mês'] = canceladas['closed_date'].dt.month
    dados_agrupados_canceladas = canceladas.groupby('mês').size().reset_index(name='Canceladas')

    return dados_agrupados_iniciadas, dados_agrupados_finalizadas, dados_agrupados_canceladas

def tabelatempos(implantacoes):
    colunastempos_ms = [item for item in implantacoes.columns if 'time' in item]
    tabelatempos = implantacoes[colunastempos_ms].copy()
    resumo_tempos = tabelatempos.describe().transpose()
    
    def limite_inferior(row):
        if row['mean'] - row['std'] > 0:
            limite = row['mean'] - row['std']
        else:
            limite = 0
        return limite

    resumo_tempos['limite_inf'] = resumo_tempos.apply(limite_inferior, axis=1)
    resumo_tempos['limite_sup'] = resumo_tempos['mean'] + resumo_tempos['std']
    resumo_tempos = resumo_tempos.round(2)
    return resumo_tempos, tabelatempos

def verificaprimeiropagamento():
    urlAssinas = 'https://api.superlogica.net/v2/financeiro/recorrencias/recorrenciasdeplanos?tipo=contratospendentes&pendentePrimeiroPagamento=true'

    headersAssinas = {
      'Accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      'app_token': app_token_assinas,
      'access_token': access_token_assinas
    }

    response = requests.get(urlAssinas, headers=headersAssinas).json()
    df = pd.DataFrame(response)
    primeiroboletopendente = df['st_identificador_plc'].drop_duplicates()
    return primeiroboletopendente

def serietemporal(df, prazo, frequencia, dias):
  df['contador'] = 1

  data_atual = datetime.now()
  datainicio = datetime(data_atual.year, 1, 1)
  datafinal = data_atual
  datainicio = Timestamp(datainicio, tz='UTC')
  datafinal = Timestamp(datafinal, tz='UTC')

  if prazo == 'Mês atual':
    datainicio = datetime(data_atual.year, data_atual.month, 1)
    datainicio = Timestamp(datainicio, tz='UTC')
  elif prazo == 'Este ano':
    datainicio = datetime(data_atual.year, 1, 1)
    datainicio = Timestamp(datainicio, tz='UTC')
  elif prazo == 'Últimos 3 meses':
    if (data_atual.month - 2) <= 0:
      delta = 12 - data_atual.month
      mes = 12 - delta
      ano = data_atual.year - 1
    else:
      mes = (data_atual.month - 2)
      ano = data_atual.year
    datainicio = datetime(ano, mes, 1)
    datainicio = Timestamp(datainicio, tz='UTC')
  elif prazo == 'Últimos 6 meses':
    if (data_atual.month - 5) <= 0:
      delta = 12 - data_atual.month
      mes = 12 - delta
      ano = data_atual.year - 1
    else:
      mes = (data_atual.month - 5)
      ano = data_atual.year
    datainicio = datetime(ano, mes, 1)
    datainicio = Timestamp(datainicio, tz='UTC')
  elif prazo == 'Últimos 12 meses':
    if (data_atual.month - 11) <= 0:
      delta = 12 - data_atual.month
      mes = 12 - delta
      ano = data_atual.year - 1
    else:
      mes = (data_atual.month - 11)
      ano = data_atual.year
    datainicio = datetime(ano, mes, 1)
    datainicio = Timestamp(datainicio, tz='UTC')

  if frequencia == 'Diária':
    frequencia = 'D'
  elif frequencia == 'Semanal':
    frequencia = 'W'
  elif frequencia == 'Mensal':
    frequencia = 'M'
  
  df = df.loc[(df[dias]>=datainicio)&(df[dias]<datafinal)]

  dados = df.summarize_by_time(
    date_column = dias,
    value_column = 'contador',
    freq = frequencia,
    agg_func = 'sum'
  )
  dados = dados.rename(columns = {dias: 'data'})
  return dados

def funil(tempos, stages):
  tempos = tempos.reset_index()
  tempos = tempos[['index', 'count']]
  tempos['index'] = tempos['index'].str.extract(r'hs_time_in_(\d+)')
  tempos = tempos.rename(columns = {'index': 'hs_pipeline_stage'})
  funil = pd.merge(stages, tempos, on='hs_pipeline_stage', how='left')
  funil['churn'] = funil['count'].diff(-1)
  funil['churn rate'] = funil['churn']*100/funil['count']
  filtro = (funil['etapa_pipeline'] != 'CANCELADAS') & (funil['etapa_pipeline'] != 'TREINAMENTOS EXTRAS')
  funil = funil[filtro]
  funil = funil.fillna(0)
  return funil



