import dash
import dash_extensions as de

from dash import Dash, dcc, html, Input, Output, State, dash_table, MATCH, ALL, callback, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

import pandas as pd
import seaborn as sms
import numpy as np
import base64
import datetime
import io
import plotly.io as pio
import json

import pymongo
from pymongo import MongoClient

from datetime import datetime
from datetime import date as dt
import time

import json
from urllib.request import urlopen

import smtplib                         
from email.message import EmailMessage  

# Importação das fontes
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,700;1,400&display=swap']

# Estilo da fonte que será utilizada
fonte = {'fontFamily': 'Poppins, sans-serif'}


# Registra como uma página de navegação
dash.register_page(__name__, path='/')

data_atual = dt.today()
horario = datetime.now().strftime("%H:%M")
mes_atual = dt.today().month


# Função para enviar alertas no e-mail https://mailtrap.io/blog/python-send-email-gmail/
def enviar_alerta(assunto, texto, destino):

    remetente = 'alerta122051@gmail.com' # Definindo o remetente

    email = EmailMessage()
    email.set_content(texto) # conteudo do email
    email['subject'] = assunto # assunto do e-mail
    email['to'] = destino # quem irá receber o e-mail
    email['from'] = remetente

    password = 'cnmyyhhketemmcel' # Senha gerada em "senhas app" do google

    # Parâmetros do servidor
    server = smtplib.SMTP('smtp.gmail.com', 587) # variável do servidor
    server.starttls()
    server.login(remetente, password)
    server.send_message(email)

    server.quit()




# Função para carregar os dados de despesa e vendas a partir do MongoDB
def carregar_dados():
    # Conectando com o servidor local
    local_vendas = MongoClient('mongodb+srv://tcc_122051:tnPQdZLXfyi3hMMw@tcc-122051.sy9tzlz.mongodb.net/test')

    # Acessando o banco de dados de vendas
    database_vendas = local_vendas['dashboardstartup']

    # Acessando a coleção de vendas
    colecao_vendas = database_vendas['baseVendas']

    # Acessando a coleção de Despesas
    colecao_despesas = database_vendas['baseDespesas']

    # Consultando a coleção e convertendo em DataFrame
    df = pd.DataFrame(list(colecao_vendas.find()))
    # Consultando a coleção e convertendo em DataFrame
    df_despesa = pd.DataFrame(list(colecao_despesas.find()))
    
    # Tratamento df
    df = df.dropna(how='all') #apagando as linhas vazias
    utila_linha_vazia = df.index[df.applymap(lambda x: x != '').all(axis=1)][-1]# Obtém o índice das últimas linhas não vazias
    df = df.drop(index=df.index[utila_linha_vazia+1:])# Remove as linhas vazias após a última linha não vazia
    df['Data da Venda'] = pd.to_datetime(df['Data da Venda'].astype(str), format='%Y-%m-%d') # Atribui o formato data para a coluna Data da Venda
    df['Quantidade'] = pd.to_numeric(df['Quantidade'], downcast ='signed') #Convertendo a coluna quantidade para inteiro
    df['Valor (R$)'] = pd.to_numeric(df['Valor (R$)'], downcast ='signed')

    # Tratamento df
    df_despesa = df_despesa.dropna(how='all') #apagando as linhas vazias
    utila_linha_vazia = df_despesa.index[df_despesa.applymap(lambda x: x != '').all(axis=1)][-1]# Obtém o índice das últimas linhas não vazias
    df_despesa = df_despesa.drop(index=df_despesa.index[utila_linha_vazia+1:])# Remove as linhas vazias após a última linha não vazia
    df_despesa['Data Pagamento'] = pd.to_datetime(df_despesa['Data Pagamento'].astype(str), format='%Y-%m-%d') # Atribui o formato data para a coluna Data Pagamento
    df_despesa['Data Vencimento'] = pd.to_datetime(df_despesa['Data Vencimento'].astype(str), format='%Y-%m-%d') # Atribui o formato data para a coluna Data Vencimento
    df_despesa['Valor (R$)'] = pd.to_numeric(df_despesa['Valor (R$)'], downcast ='signed')

    return df, df_despesa


# função para formatar os ANOS como opções de DropdownMenu
def gerar_opcoes_ano():
    df, df_despesa = carregar_dados()

    # Obtendo lista de anos do dataframe vendas
    ano_vendas = sorted(df['Data da Venda'].dt.year.unique())
    # Obtendo lista de anos do dataframe despesas
    ano_despesas = sorted(df_despesa['Data Pagamento'].dt.year.unique())
  

    # Agrupando as duas listas
    anos = sorted(list(set(ano_vendas + ano_despesas)))
    
    opcoes = [{'label': str(ano), 'value': ano} for ano in anos]
    return opcoes

# função para formatar os MESES como opções de DropdownMenu
def gerar_opcoes_mes(ano):

    df, df_despesa = carregar_dados() # Obtendo os dados da tabela
    
    # Obtendo lista de meses do dataframe vendas
    meses_vendas = sorted(df[df['Data da Venda'].dt.year == ano]['Data da Venda'].dt.month.unique())
    # Obtendo lista de meses do dataframe despesas
    meses_despesas = sorted(df_despesa[df_despesa['Data Pagamento'].dt.year == ano]['Data Pagamento'].dt.month.unique())
    

    # Agrupando as duas listas
    meses = sorted(list(set(meses_vendas + meses_despesas)))
   
    opcoes = [{'label': str(mes), 'value': mes} for mes in meses]

    return opcoes

# Função calculo para o card número de vendas
def card_numvendas(df, ano, mes, filtro='mes'):
    # CARD NUN DE VENDAS
    if filtro == 'mes':
        selecao = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]
        selecao_passado = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == (mes-1))]
    
    elif filtro == 'ano':
        selecao = df[(df['Data da Venda'].dt.year == ano)] 
        selecao_passado = df[(df['Data da Venda'].dt.year == (ano-1))]

    num_vendas = selecao['Quantidade'].count()
    ticket_m = float((selecao['Valor (R$)'].sum())/num_vendas)
    ticket_medio = 'R${:.2f}'.format(ticket_m)

    #calculando o ticket_medio do periodo anterior:
    
    num_vendas_passado = selecao_passado['Quantidade'].count()
    if num_vendas_passado == 0:
        var_nunvendas = 'nan%'
        x = 'border-start border-warning border-2' #Número de Transações
        style_var_nunvendas = 'bi bi-dash text-warning bg-light rounded' # style sem variação
    else:
        var_nunvend = ((num_vendas-num_vendas_passado)/num_vendas_passado)*100
        if var_nunvend > 0:
            x = 'border-start border-success border-2' #Número de Transações
            style_var_nunvendas = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
        elif var_nunvend < 0:
            x = 'border-start border-danger border-2' #Número de Transações
            style_var_nunvendas = 'bi bi-caret-down-fill text-danger bg-light rounded' # style para variação negativa
        else:
            x = 'border-start border-warning border-2' #Número de Transações
            style_var_nunvendas = 'bi bi-dash text-warning bg-light rounded' # style sem variação
        var_nunvendas = '{:.2f}%'.format(var_nunvend)

    ticket_medio_passado = float(selecao_passado['Valor (R$)'].sum()/num_vendas_passado)
    if ticket_medio_passado == 0:
        variacao_ticket = 'nan%'
        style_varticket = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
    else:
        variacao_tick = ((ticket_m - ticket_medio_passado)/ticket_medio_passado)*100
        if variacao_tick > 0:
            style_varticket = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
        elif variacao_tick < 0:
            style_varticket = 'bi bi-caret-down-fill text-danger bg-light rounded' # style para variação negativa
        else:
            style_varticket = 'bi bi-dash text-warning bg-light rounded' # style sem variação
        variacao_ticket = '{:.2f}%'.format(variacao_tick)
    
    return x, num_vendas, var_nunvendas, style_var_nunvendas, ticket_medio, variacao_ticket, style_varticket

# Função calculo para o card faturamento
def card_faturamentocard(df, ano, mes, filtro='mes'):
    
    # CARD FATURAMENTO
    # Verificando qual o filtro selecionado
    if filtro == 'mes':
        selecao = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]
        selecao_passado = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == (mes-1))]
    
    elif filtro == 'ano':
        selecao = df[(df['Data da Venda'].dt.year == ano)] 
        selecao_passado = df[(df['Data da Venda'].dt.year == (ano-1))]

    # Faturamento atual
    faturamento = selecao['Valor (R$)'].sum()
    fatur = 'R$ {:.2f}'.format(faturamento)

    # Faturamento passado
    faturamento_passado = selecao_passado['Valor (R$)'].sum()

    # Calculando a variação
    if faturamento_passado == 0:
        var_faturamento = 'nan%'
        card_fatur = 'border-start border-warning border-2' #Faturamento
        style_var_faturamento = 'bi bi-dash text-warning bg-light rounded' #style sem variação
    else:
        var_fatur = float((faturamento-faturamento_passado)/faturamento_passado)*100
        if var_fatur > 0:
            card_fatur = 'border-start border-success border-2' #Faturamento
            style_var_faturamento = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
        elif var_fatur < 0:
            card_fatur = 'border-start border-danger border-2' #Faturamento
            style_var_faturamento = 'bi bi-caret-down-fill text-danger bg-light rounded' # style para variação negativa
        else:
            card_fatur = 'border-start border-warning border-2' #Faturamento
            style_var_faturamento = 'bi bi-dash text-warning bg-light rounded' # style sem variação
        var_faturamento = '{:.2f}%'.format(var_fatur)

    
    return card_fatur, fatur, var_faturamento, style_var_faturamento


# Função calculo para o card despesas
def card_despesascard(df, ano, mes, filtro='mes'):

    # CARD DESPESAS
    # Verificando qual o filtro selecionado
    if filtro == 'mes':
        selecao = df[(df['Data Pagamento'].dt.year == ano) & (df['Data Pagamento'].dt.month == mes)]
        selecao_passado = df[(df['Data Pagamento'].dt.year == ano) & (df['Data Pagamento'].dt.month == (mes-1))]
    
    elif filtro == 'ano':
        selecao = df[(df['Data Pagamento'].dt.year == ano)] 
        selecao_passado = df[(df['Data Pagamento'].dt.year == (ano-1))]

    # Despesas atual
    despesas = selecao['Valor (R$)'].sum()
    desp = 'R$ {:.2f}'.format(despesas)

    # Despesas passado
    despesas_passado = selecao_passado['Valor (R$)'].sum()

    # Calculando a variação
    if despesas_passado == 0:
        var_despesas = 'nan%'
        card_desp = 'border-start border-warning border-2' #Faturamento
        style_var_despesas = 'bi bi-dash text-warning bg-light rounded' #style sem variação
    else:
        var_desp = float((despesas-despesas_passado)/despesas_passado)*100
        if var_desp > 0:
            card_desp = 'border-start border-success border-2' #Faturamento
            style_var_despesas = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
        elif var_desp < 0:
            card_desp = 'border-start border-danger border-2' #Faturamento
            style_var_despesas = 'bi bi-caret-down-fill text-danger bg-light rounded' # style para variação negativa
        else:
            card_desp = 'border-start border-warning border-2' #Faturamento
            style_var_despesas = 'bi bi-dash text-warning bg-light rounded' # style sem variação
        var_despesas = '{:.2f}%'.format(var_desp)

    
    return card_desp, desp, var_despesas, style_var_despesas

# Função calculo para o card resultado
def card_res(df, df_despesas, ano, mes, filtro='mes'):

    # CARD RESULTADO
    # Verificando qual o filtro selecionado
    if filtro == 'mes':
        # Selecionando faturamento
        selecao_faturamento = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]
        selecao_passado_faturamento = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == (mes-1))]
        # Selecionando despesas
        selecao_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano) & (df_despesas['Data Pagamento'].dt.month == mes)]
        selecao_passado_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano) & (df_despesas['Data Pagamento'].dt.month == (mes-1))]

    elif filtro == 'ano':
        # Selecionando faturamento
        selecao_faturamento = df[(df['Data da Venda'].dt.year == ano)] 
        selecao_passado_faturamento = df[(df['Data da Venda'].dt.year == (ano-1))]
        # Selecionando despesas
        selecao_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano)] 
        selecao_passado_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == (ano-1))]

    # Resultado atual
    result = selecao_faturamento['Valor (R$)'].sum() - selecao_despesas['Valor (R$)'].sum()
    resultado = 'R$ {:.2f}'.format(result)

    # resultado passado
    result_passado = selecao_passado_faturamento['Valor (R$)'].sum() - selecao_passado_despesas['Valor (R$)'].sum()

    # Calculando a variação
    if result_passado == 0:
        var_resultado = 'nan%'
        card_result = 'border-start border-warning border-2' #Faturamento
        style_var_resultado = 'bi bi-dash text-warning bg-light rounded' #style sem variação
    else:
        var_resultado = float((result-abs(result_passado))/abs(result_passado))*100
        
        if var_resultado > 0:
            card_result = 'border-start border-success border-2' #Faturamento
            style_var_resultado = 'bi bi-caret-up-fill text-success bg-light rounded' # style para variação positiva
        elif var_resultado < 0:
            card_result = 'border-start border-danger border-2' #Faturamento
            style_var_resultado = 'bi bi-caret-down-fill text-danger bg-light rounded' # style para variação negativa
        else:
            card_result = 'border-start border-warning border-2' #Faturamento
            style_var_resultado = 'bi bi-dash text-warning bg-light rounded' # style sem variação
        
        if result_passado >= 0:
            var_resultado = '{:.2f}% no lucro'.format(var_resultado)
        else:
            var_resultado = '{:.2f}% no prejuízo'.format(var_resultado)

    return card_result, resultado, var_resultado, style_var_resultado


#Para usar a base de dados dos estados brasileiros vamos abrir o banco de dados através de um webscraping
with urlopen('https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson') as response:
 brasil = json.load(response) # notação Javascrip 
# Vamos reunir as informações dos dados brazil.json com os dados da tabela
id_estado = {}
for feature in brasil ['features']:
 feature['id'] = feature['properties']['name']
 id_estado[feature['properties']['sigla']] = feature['id']
# id_estado será usado posteriormente para traduzir as UF em estados.

# Função para gerar o mapa das vendas
def mapa(df, ano, mes, filtro = 'mes'):

    if filtro == 'mes':
        selecao = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]

    else:
        selecao = df[(df['Data da Venda'].dt.year == ano)] 

    # Contabilizando a quantidade de vendas por UF
    vendas_uf = selecao.groupby('UF', as_index=False)['Quantidade', 'Valor (R$)'].sum()
    vendas_uf.columns = ['UF', 'Quantidade de vendas', 'Volume Transacionado (R$)'] # Alterando o nome da coluna
    vendas_uf['UF'] = vendas_uf['UF'].map(id_estado)

    # Formatação dos valores para hover data
    #vendas_uf['Volume Transacionado (R$)'] = (vendas_uf['Volume Transacionado (R$)'].apply(lambda x: '{:.2f}'.format(x)))
    #vendas_uf['Quantidade de vendas'] = vendas_uf['Quantidade de vendas'].astype(int)

    # Fazedno o mapa
    fig = px.choropleth_mapbox(
                vendas_uf,  # DataFrame com a quantidade de vendas por UF
                locations='UF',  # Coluna com as UFs para aparecer no mapa
                geojson = brasil, 
                color='Volume Transacionado (R$)',  # Coluna com os valores para colorir o mapa
                labels={'Valor (R$)':'Volume transacionado'}, 
                hover_name="UF", # Mostra o nome do estado ao passar o mouse sobre
                hover_data =['Quantidade de vendas', 'Volume Transacionado (R$)'],
                mapbox_style = "open-street-map", # Estilo do mapa "open-street-map" - "carto-positron"
                center={"lat":-14, "lon": -55},
                zoom=2.5,
                color_continuous_scale=px.colors.sequential.RdBu_r, # Estilo da cor
                # Inverti para que as cores quentes representassem o maior valor transacionado (R$).
                opacity=0.8,
                )
    
    fig.update_coloraxes(colorbar=dict(
    title='Volume Transacionado',
    tickprefix='R$',
    thickness=15,
    lenmode='fraction',
    len=0.6,
    x=0,  # Ajuste a posição horizontal da barra lateral aqui
    y=0.6,   # Ajuste a posição vertical da barra lateral aqui
    yanchor='middle',
    ))

    #fig.update_geos(fitbounds = "locations", visible = False)
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        font=dict(
        family="Monteserrat",
        size=14),
        height= 600
    )

    return fig



# Função para gerar o gráfico de faturamento x despesas
def fat_desp(df, df_despesas, ano, mes, filtro = 'mes'):

    if filtro == 'mes':
        selecao = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]
        selecao_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano) & (df_despesas['Data Pagamento'].dt.month == mes)]

    else:
        selecao = df[(df['Data da Venda'].dt.year == ano)]
        selecao_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano)]

    faturamento = selecao.groupby('Data da Venda', as_index=False)['Valor (R$)'].sum()
    faturamento.columns = ['Data', 'Faturamento']

    # Calcula o total das despesas no mesmo período de tempo do faturamento
    despesas = selecao_despesas.groupby('Data Pagamento', as_index=False)['Valor (R$)'].sum()
    despesas.columns = ['Data', 'Despesas']
    

    # Contruindo o gráfico
    fig = go.Figure()
    # Adiciona a série de dados de faturamento ao gráfico
    fig.add_trace(
        go.Scatter(x=faturamento['Data'], y=faturamento['Faturamento'],
                   name='Receita',
                   line=dict(color='#31729C', width=2),
                   hovertemplate='Data: %{x}<br>Receita: R$ %{y:.2f}')
    )

    # Adiciona a série de dados de despesas ao gráfico
    fig.add_trace(
        go.Scatter(x=despesas['Data'], y=despesas['Despesas'],
                   name='Despesas',
                   line=dict(color='#FF3D27', width=2),
                   hovertemplate='Data: %{x}<br>Despesas: R$ %{y:.2f}')
    )

    # Layout do gáfico
    fig.update_xaxes(title="Data", showgrid=True, gridcolor='lightgray', title_font=dict(size=18, family='Poppins, sans-serif'))
    fig.update_yaxes(title="Volume (R$)", showgrid=True, gridcolor='lightgray', title_font=dict(size=18, family = 'Poppins, sans-serif'))
    fig.update_layout(template ='plotly_white', 
                    title={
                        'text': "Receita x Gastos",
                        'font': {'size': 24, 'family': 'Poppins, sans-serif'},
                        'x': 0.5,
                        'y': 0.9
                    }
    )
                      
    return fig


# Função para gerar o gráfico de pizza do mapa
def pie_chart_mapa(df, ano, mes, filtro = 'mes'):    

    if filtro == 'mes':
        selecao = df[(df['Data da Venda'].dt.year == ano) & (df['Data da Venda'].dt.month == mes)]

    else:
        selecao = df[(df['Data da Venda'].dt.year == ano)]

    # Contabilizando a quantidade de vendas por código de produto
    quantidade_pie = selecao.groupby('Cod_Produto', as_index=False)['Quantidade'].sum()
    
    pivot_table = pd.pivot_table(selecao, 
                             columns='Cod_Produto', 
                             index='UF', 
                             values='Quantidade', 
                             aggfunc='sum')


    specs = [[{'type':'pie'}], [{"type": "heatmap"}]]
    fig = make_subplots(rows=2, cols=1, specs=specs, shared_yaxes = True,
                        row_heights=[0.5, 0.5], vertical_spacing=0.2,
                        )

    fig.add_trace(go.Pie(values=quantidade_pie['Quantidade'], 
                      labels=quantidade_pie['Cod_Produto'],
                      marker_colors=px.colors.sequential.RdBu, #Inverti para que as cores quentes representassem o maior valor transacionado (R$).
                      hole=0.4,
                      showlegend=True,
                      textinfo='label+percent',
                      hovertemplate='Produto %{label}: %{percent:.1%} <br>Quantidade: %{value}'),
                       
              row=1, col=1
        )
    
    fig.add_trace(go.Heatmap(
                    z=pivot_table.values,  # Dados da tabela pivoteada
                    x=pivot_table.columns.tolist(),  # Nomes das colunas
                    y=pivot_table.index.tolist(),  # Nomes das linhas
                    colorscale='RdBu',  # Esquema de cores
                    reversescale=True,  # Inverte a escala de cores
                    showlegend = False,
                    showscale=True,
                    texttemplate='%{z}',
                    hovertemplate = 'Cod_produto: %{x}<br>Quantidade: %{z}'
                ),
            row=2, col=1
        )

    fig.update_layout(
        font=dict(size=14, family='Poppins, sans-serif'),
        title={
            'text': "Quantidade x Produto",
            'font': {'size': 24, 'family': 'Poppins, sans-serif'}
        },
        template='plotly_white',
        height = 600,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=10, t=80, b=60), #Margim do subplot
        legend=dict(
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.35,
            font=dict(size=12)
        ),
    )
    

    # Ajustando a legenda do gráfico de pizza
    fig.update_traces(
        selector=dict(type='pie'), 
        textfont=dict(size=12)
    )



    # Ajustando a legenda do mapa de calor
    fig.update_traces(
        selector=dict(type='heatmap'),  
        colorbar=dict(
            len=0.6, 
            y=0.2, 
            x = 1.35, 
            thickness=15, 
            tickfont=dict(size=12))
    )


    # Definindo as fontes dos eixos
    fig.update_xaxes(title_font=dict(size=16, family='Poppins, sans-serif'))
    fig.update_yaxes(title_font=dict(size=16, family='Poppins, sans-serif'))
    

    return fig


def pie_ToDo(children):
    # Definindo os parâmetros para contabilizar o gráfico de pizza
    global pendente, concluido, atrasado
    pendente = 0
    concluido = 0
    atrasado = 0

    if children is not None:
        for i in range(len(children)):
            # Condição para pendente
            if 'bi bi-record-fill text-warning' in (children[i]['props']['children'][0]['props']['children'][2]['props']['className']):
                pendente = pendente + 1
            # Condição para concluido
            elif 'bi bi-record-fill text-success' in (children[i]['props']['children'][0]['props']['children'][2]['props']['className']):
                concluido = concluido + 1
            # Condição para atrasado
            elif 'bi bi-record-fill text-danger' in (children[i]['props']['children'][0]['props']['children'][2]['props']['className']):
                atrasado = atrasado + 1

    # Definindo as cores
    cores = ['#18BC9C', '#F39C12', '#E74C3C']

    # Criando gráfico de pizza
    fig = go.Figure(
    [
        go.Pie(labels=['Concluídas', 'Pendentes', 'Atrasadas'], 
            values=[concluido, pendente, atrasado],
            marker_colors=cores, #Inverti para que as cores quentes representassem o maior valor transacionado (R$).
            hole=0.4,
            showlegend=True,
            textinfo='label+percent+value'
        )
    ])

    fig.update_layout(
        font=dict(size=14, family='Poppins, sans-serif'),
        title={
            'text': "Tarefas",
            'font': {'size': 24, 'family': 'Poppins, sans-serif'}
        },
        template='plotly_white',
    )

    return fig, atrasado

# Função que conta a quantidade de períodos do coorte
def coorte_periodo(data):
    data['coorte_periodo'] = np.arange(len(data)) + 1
    return data

# Card quantidade de vendas
card_numerovendas = dbc.Card(id = 'card-quantidadeVendas', children=[
            dbc.CardImg(
                src= "/assets/QuantidadeT.png",
                top = True,
                style={'opacity': '1'}
            ),
            dbc.CardImgOverlay(
                dbc.CardBody([
                    html.H4("Número Transações", style = {'color': 'white', 'fontWeight': 'bold', 'margin': '0px'}),
                    html.Div([
                        html.P(id = 'quantidadeVendas', children = [],
                           style={'color': 'white', 'font-size': '22px', 'display': 'inline-block', 'width': '50%'}), # número de vendas

                        html.I(id = 'variacao-quantidadeVendas', style={'color': 'white', 'font-size': '12px', 'margin': '0px', 
                                                               'display': 'inline-block', 'fontWeight': 'bold'}),  #número de transações
                    ]),
                    html.Div(
                    [
                        html.P(['Ticket Médio'], style={'color': 'white', 'fontWeight': 'bold', 'margin': '0px'}),
                        html.Div([
    
                            html.I(id = 'ticket-medio', style={'color': 'white', 'font-size': '16px', 'margin': '0px', 
                                                               'display': 'inline-block', 'width': '50%'}),  #ticket_medio
                            
                            html.I(id = 'variacao-ticket-medio', style={'color': 'white', 'font-size': '16px', 'margin': '0px',
                                                                        'display': 'inline-block', 'fontWeight': 'bold', 'font-size': '12px'})  #Variação ticket_medio
                        ])
                        
                    ])
                    
                ])
            )
        ], style = {'width': '19rem', "fontFamily": fonte, 'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)'}
        )

# Card faturamento
card_faturamento = dbc.Card(id = 'card-faturamento-style', children=[
            dbc.CardImg(
                src= "/assets/vendas.png",
                top = True,
                style={'opacity': '1'}
            ),
            dbc.CardImgOverlay(
                dbc.CardBody([
                    html.H4("Faturamento", style = {'color': 'white', 'fontWeight': 'bold'}),
                    html.Div([
                        html.P(id = 'faturamento', children = [],
                           style={'color': 'white', 'font-size': '22px', 'width': '100%', 'margin': '0'}), # Faturamento
                        
                        html.I(id = 'variacao-faturamento', style={'color': 'white', 'font-size': '12px', 'margin': '0px', 
                                                                 'width': '35%', 'fontWeight': 'bold','margin-top':'0'}) # Faturamento
                    ])
                    
                ])
            )
        ], style = {'width': '19rem', "fontFamily": fonte, 'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)'}
        )

# Card valor (R$) despesas
card_despesas = dbc.Card(id = 'card-despesas-style', children=[
            dbc.CardImg(
                src= "/assets/despesas.png",
                top = True,
                style={'opacity': '1'}
            ),
            dbc.CardImgOverlay(
                dbc.CardBody([
                    html.H4("Gastos", style = {'color': 'white', 'fontWeight': 'bold'}),
                    html.Div([
                        html.P(id = 'despesas', children = [],
                           style={'color': 'white', 'font-size': '22px', 'width': '100%', 'margin': '0'}), # Despesas
                        
                        html.I(id = 'variacao-despesas', style={'color': 'white', 'font-size': '12px', 'margin': '0px', 
                                                                 'width': '35%', 'fontWeight': 'bold','margin-top':'0'}) # Despesas
                    ])
                ])
            )
        ], style = {'width': '19rem', "fontFamily": fonte, 'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)'}
        )


# Card valor (R$) Resultado
card_resultado = dbc.Card(id = 'card-resultado-style', children=[
            dbc.CardImg(
                src= "/assets/lucro.png",
                top = True,
                style={'opacity': '1'}
            ),
            dbc.CardImgOverlay(
                dbc.CardBody([
                    html.H4("Resultado", style = {'color': 'white', 'fontWeight': 'bold'}),
                    html.Div([
                        html.P(id = 'resultado', children = [],
                           style={'color': 'white', 'font-size': '22px', 'width': '100%', 'margin': '0'}), # Resultado
        
                        html.I(id = 'variacao-resultado', style={'color': 'white', 'font-size': '12px', 'margin': '0px', 
                                                                 'width': '35%', 'fontWeight': 'bold','margin-top':'0'})  #Variação percentual
                    ])
                    
                ])
            )
        ], style = {'width': '19rem', "fontFamily": fonte, 'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)'}
        )



# Grupo do botão de análise 
button_group = dbc.ButtonGroup(
    [
        dbc.DropdownMenu(
            children = [dbc.DropdownMenuItem("Não há tabela", disabled=True)],
            label="Ano",
            id="filtro-ano",
            group=True,
            color = 'primary',
        ),

        dbc.DropdownMenu(
            children = [dbc.DropdownMenuItem("Não há tabela", disabled=True)],
            label="Mês",
            id="filtro-mes",
            group=True,
            color = 'primary'
        ),
    ],
    size="sm",
    style={'position':'fixed', 'z-index': '9999'} 
    #Propriedade z-index para colocar o buttongroup na fente das 
    #outras divs
    
)



layout = html.Div(
    [   
    
    # Armazena o valor do ano selecionado
    dcc.Store(id='store_ano', storage_type='local'),
    # Armazena o valor do mes selecionado
    dcc.Store(id='store_mes', storage_type='local'),
    # Armazena o valor do tamanho do dict opcoes_mes. Usado na logica de calcular TODOS OS MESES
    dcc.Store(id='store_mes-aux', storage_type='local'),
    # Armazena as taks cadastrados na lista To Do
    dcc.Store(id='store_ToDotask', storage_type='local'),
    # Armazena quando foi o ultimo email enviado 
    dcc.Store(id='ultimo_envio', storage_type='local'),
    # Armazena quantas atividades estão atrasadas 
    dcc.Store(id='atraso', storage_type='local'),
    # Armazena o tamanho das tasks
    dcc.Store(id='tamanho_task', storage_type='local'),

    # Estrutura que rebece o botão de dúvida e Slider
    html.Div(
        id = 'inicio', 
        children = [
    
            html.Div([
                html.Div(
                    button_group,
                    style={'margin-top':'10px', 'margin-left':'7px'}
                ),

                dbc.Button("Dúvida?", id="abrir", color = 'warning', outline = True, n_clicks=0,
                        style={'margin-top':'1.5vh', }),
                        
            ], style={'margin-top': '10px', 'display': 'flex',  'justify-content':'space-between'}
            ),

            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Dúvida",  style ={'font-family': fonte, 'color': 'white', 'fontWeight': 'bold'}), 
                                style = {'background-color': '#2C3E50'}),
                                
                dbc.ModalBody("A partir desta ferramente, você poderá analisar dados financeiros."
                    " Para começar, basta navegar para a página *VENDAS ou *DESPESAS e carregar os dados"
                    " a serem analisados."
                    " Em cada uma das páginas você irá encontrar um modelo de análise para download", 
                    style={'color':'black', 'text-align': 'justify', 'text-justify': 'inter-word',
                           'font-family': fonte}
                ),

                dbc.ModalFooter(
                    dbc.Button(
                        "Fechar", id="fechar", color = 'danger', n_clicks=0
                    ),
                    style = {'background-color': 'white'}),
            ],
            id="pop-up",
            is_open=False,
            )
        ], 
        style={'margin-rigth': '1vh', 'margin-right':'15px'
        }
        ),
    dcc.Loading(
        id = 'loading',
        children = [
    
        # Dentro dessa Div vamos criar os cards que irão conter informações
        dbc.Row([
            dbc.Col(card_numerovendas, style={"display": "flex", "justify-content": "center"}), 
            dbc.Col(card_faturamento, style={"display": "flex", "justify-content": "center"}),
            dbc.Col(card_despesas, style={"display": "flex", "justify-content": "center"}), 
            dbc.Col(card_resultado, style={"display": "flex", "justify-content": "center"})
        ], 
            style={
                "margin": "auto",
                "display": "flex",
                "justify-content": "center",
                "padding": "2vh",
            },
        ),

        html.P(),
        html.Hr(),

        html.Div([
            dcc.Graph(id='faturamento_despesas', style={'background-color': '#f5f5f5',
                                                'margin-top':'30px', 'margin-left':'10px',
                                                'margin-right':'10px',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                'width': '99%'
                                                }
            ),

        ], style={'display':'flex', 'justify-content': 'center'}),


        html.Div([
    
            dcc.Graph(id = 'barras_resultado', style={'margin-top':'30px', 'margin-left':'10px',
                                                'margin-right':'10px',
                                                'width':'63%',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                }),

            dcc.Graph(id = 'pie_despesas', style={'margin-top':'30px', 'margin-right':'10px',
                                                'margin-left':'30px',
                                                'width':'33%',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                }
            )
        ], style = {'display': 'flex', 'justify-content':'center'}),

        html.Div([
            dcc.Graph(id='mapa_grafico', style={'background-color': '#f5f5f5',
                                                'margin-top':'30px', 'margin-left':'10px',
                                                'margin-right':'10px',
                                                'width':'63%',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                }
            ),
            dcc.Graph(id = 'pie-chart-mapa', style={'background-color': '#2C3E50',
                                                'margin-top':'30px', 'margin-right':'10px',
                                                'margin-left':'30px',
                                                'width':'33%',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                }
            )

        ], style={'display': 'flex', 'justify-content': 'center', 'width': '100%'}
        ),

        # Análise Coorte
        html.Div([
            
            dcc.Graph(id = 'atividade-clientes', style = {'background-color': '#2C3E50',
                                                            'margin-top':'30px', 'margin-right':'10px',
                                                            'margin-left':'10px',
                                                            'width':'51%',
                                                            'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)'}),

            dcc.Graph(id = 'coorte', style = {'background-color': '#2C3E50',
                                                'margin-top':'30px', 'margin-right':'10px',
                                                'margin-left':'30px',
                                                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                                                'width': '45%'}),
                            
            

        ], style={'display': 'flex', 'justify-content': 'center', 'width': '100%', 'height':'33rem'}
        ),

        ],
        type = 'graph',
        
        style = {'position': 'fixed', 'top': '50%', 'left': '50%', 
                 'transform': 'translate(-50%, -50%)'}
        # Deixando o simbolo de carregamento no centro da tela
        # translate é usada para ajustar a posição do componente no
        # centro exato da janela do navegador.
    ),



    # To Do List
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H1(children = ['To do list\xa0'], style={'color': 'white', "fontFamily": fonte, 'margin-top':'50px', 'margin-left':'20px'}),
                    html.I(className = "bi bi-check-all", style={'font-size':'3.5rem', 'margin-top':'40px', 'color':'white'}),
                ], style={'display':'flex'}
                ),
                        
                html.Div(
                [
                    html.H4(id = 'dia', children = [], style={'margin-left':'30px', 'width': '9rem', 'fontFamily': fonte, 'color': 'white'}),
                    html.H4(id = 'hora', children = [], style={'width':'5rem', 'font-size':'18px', 'margin-top':'6px', 'fontFamily': fonte, 'color': 'white'})
                ], style={'display':'flex', 'width': '100%'}
                ),
            ], style={'background': 'linear-gradient(to right, #2C3E50, #46719C, #65809C)', 'margin-bottom': '20px'}
            ),

            #Div que recebe uma lista do To Do 
            html.Div([
                html.Ul(id='lista-ToDo', className='list', style={  'max-height': '300px', 'overflow-y': 'auto'}),
                
            ]),

            #Div que recebe o campo de preenchimento
            html.Div([
        
                # Botão de adicionar tarefa
                dbc.Button('Add tarefa', id="add-task", className="bi bi-plus-lg",  
                    color = 'info', outline = True, n_clicks=None, size= 'sm',
                    style={'margin':'10px', 'width': '15%'}),

                # Recebe texto da tarefa
                dbc.Input(id= 'input-ToDo', type='text', placeholder='Adicione uma tarefa',
                        style = {'width': '75%', 'margin':'10px'}),
                
                # Botão para abrir o calendário
                dbc.Button(id = 'calendario', className='bi bi-calendar-check', size = 'sm',
                        style= {'color': 'black', 'font-size': '20px', 'margin-right': '7px'},
                            n_clicks=None, outline = True),
                
                html.Div(id = 'calendario_data', children=[
                    html.Div(children = [dcc.DatePickerSingle(id='data_ToDo')],
                            hidden = True
                    )
                ])
            
            ], style={'width': '100%', 'display':'flex',
                    'justify-content': 'flex-start'}
            ),

        ], 
            style={
                'width':'63%', 'background-color': 'white', 
                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                'margin-top':'30px', 'margin-left':'10px', 'margin-right':'10px'
            }
        ),

        dcc.Graph(id= 'grafico-ToDo', style={'width':'33%', 'background-color': 'white', 
                'box-shadow': '3px 3px 10px 2px rgba(0, 0, 0, 0.2)',
                'margin-top':'30px', 'margin-left':'30px', 'margin-right':'10px'})
        

    ], style={'display':'flex', 'justify-content': 'center', 'margin-bottom': '50px'}
    ),

    dcc.Interval(
        id='dia_hora',
        interval=1000 * 1, # intervalo em milissegundos
        n_intervals=0
    ),

    dcc.Interval(
        id='interval-component',
        interval=1000*60 * 60, # intervalo em milissegundos
        n_intervals=0
    ),
    # Tempo e-mail
    dcc.Interval(
        id='tempo_email',
        interval=1000 * 10, # intervalo em milissegundos
        n_intervals=0
    ),

]
)

# Callback para abrir e fechar o botão de dúvida
@callback(
    Output("pop-up", "is_open"),
    [Input("abrir", "n_clicks"), Input("fechar", "n_clicks")],
    State("pop-up", "is_open"),
)
def pop_up(n1, n2, estado):
    if n1 or n2:
        return not estado
    return estado


@callback(
        Output('card-quantidadeVendas', 'className'),
        Output('quantidadeVendas', 'children'),
        Output('variacao-quantidadeVendas', 'children'),
        Output('variacao-quantidadeVendas', 'className'),
        Output('ticket-medio', 'children'),
        Output('variacao-ticket-medio', 'children'),
        Output('variacao-ticket-medio', 'className'),
        Output('card-faturamento-style', 'className'),
        Output('faturamento', 'children'),
        Output('variacao-faturamento', 'children'),
        Output('variacao-faturamento', 'className'),
        Output('card-despesas-style', 'className'),
        Output('despesas', 'children'),
        Output('variacao-despesas', 'children'),
        Output('variacao-despesas', 'className'),
        Output('card-resultado-style', 'className'),
        Output('resultado', 'children'),
        Output('variacao-resultado', 'children'),
        Output('variacao-resultado', 'className'),
        Output('store_ano', 'data'),
        Output('store_mes', 'data'),
        Output('store_mes-aux', 'data'),
        Output('faturamento_despesas', 'figure'),
        Output('mapa_grafico', 'figure'),
        Output('pie-chart-mapa', 'figure'),
        Input('interval-component', 'interval'),
        Input('store_ano', 'data'),
        Input('store_mes', 'data'),
        Input('store_mes-aux', 'data'),
        Input({'type': 'ano-dropdown', 'index': ALL}, 'n_clicks'),
        Input({'type': 'mes-dropdown', 'index': ALL}, 'n_clicks'),
        Input({'type': 'mes-dropdown-total', 'index': ALL}, 'n_clicks'),
        State({'type': 'ano-dropdown', 'index': ALL}, 'id'),
        State({'type': 'mes-dropdown', 'index': ALL}, 'id'),
        prevent_initial_call=True
)

def carregar_output(intervalo, ano, mes, mes_aux, n_ano, n_mes, n_mes_total, ano_selecionado, mes_selecionado):

    df, df_despesa = carregar_dados() #Chamando a função que carrega os dados a partir do MongoDB
    
    # Obtendo o ano e o mês selecionado
    # Obtenha o id do ano selecionado no filtro-ano
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Decodifica o objeto retornando o index. 
    input_id = json.loads(triggered_id)# Neste caso retorna a posição em que o botao delete foi assionado.
    
    if input_id['type'] == 'ano-dropdown':
        ano_selecionado = gerar_opcoes_ano()[input_id['index']]['value'] # Retorna o valor e o label do dropdown ano selecionado
        ano = ano_selecionado
        
        noupdate = dash.no_update

        return noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, noupdate, ano, noupdate, noupdate, noupdate, noupdate, noupdate
    
    if input_id['type'] == 'mes-dropdown':
        opcoes_mes = gerar_opcoes_mes(ano)
        mes_aux = len(opcoes_mes)
        mes = opcoes_mes[input_id['index']]['value']
        
        #return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, mes

    # Calcula as estatísticas

    if (input_id['index']) > mes_aux: #Condição se o usuário clicar em "Todos os meses"
        
        # CARD NUN DE VENDAS
        x, num_vendas, var_nunvendas, style_var_nunvendas, ticket_medio, variacao_ticket, style_varticket = card_numvendas(df, ano, mes, filtro = 'ano')

        # CARD FATURAMENTO
        card_fatur, fatur, var_fatur, style_var_fatur = card_faturamentocard(df, ano, mes, filtro = 'ano')
        
        # CARD DESPESAS
        card_desp, desp, var_despesas, style_var_despesas = card_despesascard(df_despesa, ano, mes, filtro = 'ano')

        # CARD RESULTADO
        card_result, result, var_resultado, style_var_resultado = card_res(df, df_despesa, ano, mes, filtro='ano')
       
        # Gráfico Faturamento X Despesas
        fig_fatdesp = fat_desp(df, df_despesa, ano, mes, filtro='ano')

        # Mapa
        fig_mapa = mapa(df, ano, mes, filtro='ano')   

        # Pie chart mapa
        fig_pie_map = pie_chart_mapa(df, ano, mes, filtro='ano')

    else: # Condição se o usuário selecionar um mês específico 
        # CARD NUN DE VENDAS
        x, num_vendas, var_nunvendas, style_var_nunvendas, ticket_medio, variacao_ticket, style_varticket = card_numvendas(df, ano, mes, filtro = 'mes')

        # CARD FATURAMENTO
        card_fatur, fatur, var_fatur, style_var_fatur = card_faturamentocard(df, ano, mes, filtro = 'mes')
        
        # CARD DESPESAS
        card_desp, desp, var_despesas, style_var_despesas = card_despesascard(df_despesa, ano, mes, filtro = 'mes')
        
        # CARD RESULTADO
        card_result, result, var_resultado, style_var_resultado = card_res(df, df_despesa, ano, mes, filtro='mes')
        
        # Gráfico Faturamento X Despesas
        fig_fatdesp = fat_desp(df, df_despesa, ano, mes, filtro='mes')

        # Mapa
        fig_mapa = mapa(df, ano, mes, filtro='mes')   

        # Pie chart mapa
        fig_pie_map = pie_chart_mapa(df, ano, mes, filtro='mes')


    print('ano analisado {}'.format(ano))
    print('mes analisado {}'.format(mes))

    return x, num_vendas, var_nunvendas, style_var_nunvendas, ticket_medio, variacao_ticket, style_varticket, card_fatur, fatur, var_fatur, style_var_fatur, card_desp, desp, var_despesas, style_var_despesas, card_result, result, var_resultado, style_var_resultado, ano, mes, mes_aux, fig_fatdesp, fig_mapa, fig_pie_map



# Callback para gerar as opçãoes de ano de acordo com a tabela vendas
@callback(
    Output('filtro-ano', 'children'),
    Input('interval-component', 'interval')
)

def atualizar_opcoes_ano(n):
    opcoes_ano = gerar_opcoes_ano()
    
    children_anos = [
        dbc.DropdownMenuItem(opcao['label'], id={'index': i, 'type': 'ano-dropdown'}) for i, opcao in enumerate(opcoes_ano)
    ]

    return children_anos



@callback(
    Output('filtro-mes', 'children'),
    Input({'type': 'ano-dropdown', 'index': ALL}, 'n_clicks'),
    State({'type': 'ano-dropdown', 'index': ALL}, 'id'),
    prevent_initial_call=True
)
def atualizar_opcoes_mes(n, ids):

    # Obtenha o id do ano selecionado no filtro-ano
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]

    # Decodifica o objeto retornando o index. 
    input_id = json.loads(triggered_id)["index"]# Neste caso retorna a posição em que o botao delete foi assionado.

    ano_selecionado = gerar_opcoes_ano()[input_id] # Retorna o valor e o label do dropdown ano selecionado no seguinte formato:
    # ex: {'label': '1998', 'value': 1998}

    # Gere as opções de mês correspondentes ao ano selecionado
    opcoes_mes = gerar_opcoes_mes(ano_selecionado['value'])
    
    children_meses = [
        dbc.DropdownMenuItem(opcao['label'], id={'index': i, 'type': 'mes-dropdown'}) 
        for i, opcao in enumerate(opcoes_mes)
        
    ] + [
        dbc.DropdownMenuItem(divider=True),
        dbc.DropdownMenuItem("Todos os meses", id={'index': len(opcoes_mes)+1, 'type': 'mes-dropdown-total'}) 
    ]
    
    return children_meses


# Callback para fazer atualizar o label do dropdown ano
@callback(
    Output("filtro-ano", 'label'),
    Output("filtro-mes", 'label'),
    Input('store_ano', 'data'),
    Input('store_mes', 'data'),
    Input('store_mes-aux', 'data'),
    Input({'type': 'mes-dropdown', 'index': ALL}, 'n_clicks'),
    Input({'type': 'mes-dropdown-total', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def atualizar_dropdown_label(ano, mes, mes_aux, pos_mes, pos_mes_aux):

    ano = 'Ano: '+str(ano)
    mes = 'Mês: '+str(mes)

    # Obtenha o id do ano selecionado no filtro-ano
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    
    # Decodifica o objeto retornando o index. 
    input_id = json.loads(triggered_id)
    
    if (input_id['index']) > mes_aux:
        mes = 'Mês: full'

    return ano, mes

# Callback para verificar a atividade dos clientes
@callback(
    Output('coorte', 'figure'),
    Output('atividade-clientes', 'figure'),
    Input('store_ano', 'data')
)
# Análise coorte
def func_coorte(ano):
    # Obtendo o DataFrame
    df, _ = carregar_dados() # Obtendo os dados da tabela
    # Selecionando os dados de acordo com o ano
    selecao = df[(df['Data da Venda'].dt.year == ano)]
    # Criando uma coluna nova contendo apenas o mês e o ano analisado.
    selecao['Data'] = selecao['Data da Venda'].apply(lambda x: x.strftime('%Y-%m'))
    
    #Agora vamos gerar um id para cada cliente
    # Obtendo a lista de CPF do DataFrame
    num_cpf = selecao['CPF'].unique()
    # Obter os id para cada CPF
    customer_ids = pd.factorize(num_cpf)[0]
    # Criar um dicionário que mapeia cada CPF a um id
    cpf_id = dict(zip(num_cpf, customer_ids))
    # Casar os CPFs no DataFrame aos ids correspondentes
    selecao['customer_id'] = selecao['CPF'].map(cpf_id)
    # Agora vou transformar o customer_id em index
    selecao.set_index('customer_id', inplace = True)
    # coorte receberá a primeira data que um determinado cliente paraceu na loja 
    selecao['coorte'] = selecao.groupby(level = 0)['Data da Venda'].min().apply(lambda x: x.strftime('%Y-%m'))
    selecao.reset_index(inplace = True)
   
    #Agrupando coorte e Data. Assim vamos poder ver na coluna coorte quando
    #o cliente comprou pela primeira vez na loja e na coluna Data as demais datas
    #que o cliente voltou a comprar na loja 
    coorte = selecao.groupby(['coorte', 'Data'])
    # Contando os diferente customers ids
    coorte = coorte.agg({'customer_id': pd.Series.nunique})
    coorte.rename(columns = {'customer_id': 'total_clientes'}, inplace = True)
    
    #Agora vamos obter a quantidade de períodos de cada coorte, isto é, quantos meses os cliente compraram
    coorte = coorte.groupby(level = 0).apply(coorte_periodo)
   
    #Configurando novamente o index
    coorte.reset_index(inplace = True)
    coorte.set_index(['coorte','coorte_periodo'], inplace = True)
    
    
    coorte_tamanho = coorte['total_clientes'].groupby(level = 0).first()
    

    churn = coorte['total_clientes'].unstack(0).divide(coorte_tamanho, axis = 1)
    
    # COnstruindo o gráfico Heatmap
    fig = go.Figure()

    fig.add_trace( 
        go.Heatmap(
            z=churn.T.values,  # Dados da tabela pivoteada
            #x=churn.T.columns.tolist(),  # Nomes das colunas
            #y=churn.T.index.tolist(),  # Nomes das linhas
            colorscale='RdBu_r',  # Esquema de cores
            showlegend = False,
            showscale=True,
            hovertemplate = 'Atividade: %{z:.2%}<br>Data: %{y}',
            texttemplate='%{z:.0%}',
            textfont=dict(size=12, family= 'Poppins, sans-serif')
        )
    )

    fig.update_layout(
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(0,13)), # Definindo a posição
            ticktext=['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'], # definindo o label
            autorange='reversed' # Inverter o eixo Y
        ),

        xaxis=dict(
            tickmode='array',
            tickvals=list(range(0,12)), # Definindo a posição
            ticktext=['{}'.format(i) for i in range(1,13)] # definindo os labels das posições
        ),

        xaxis_title='Período',
        yaxis_title='Data', 

        template='plotly_white', # Estilo templete

        title={
            'text': 'Atividade dos clientes',
            'font': {'size': 24, 'family': 'Poppins, sans-serif'}
        },
    )

    # Ajustando a legenda do mapa de calor
    fig.update_traces(
        selector=dict(type='heatmap'),  
        colorbar=dict(
            len=1, 
            y=0.5, 
            x = 1.07, 
            thickness=20, 
            tickfont=dict(size=12))
    )


    # Contruindo o gráfio line
    coorte.reset_index(inplace = True)
    coorte.set_index(['coorte_periodo'], inplace = True)

    # Definindo o gráfico
    fig_line = px.line(coorte, x = 'coorte', y = 'total_clientes')

    # Editando o gráfico
    fig_line.update_layout(
        template='plotly_white',
        title={
            'text': 'Atividade dos clientes',
            'font': {'size': 24, 'family': 'Poppins, sans-serif'}
        },
        xaxis_title='Data',
        yaxis_title='Quantidade de clientes', 
        
    )
    # Editando o eixo x
    fig_line.update_xaxes(showgrid=True, gridcolor='lightgray', tickangle=45, title_font=dict(size=16, family='Poppins, sans-serif'))
    # Editando o eixo y
    fig_line.update_yaxes(showgrid=True, gridcolor='lightgray', title_font=dict(size=16, family = 'Poppins, sans-serif'))

    # Editando a cor da linha do gráfico
    fig_line.update_traces(line_color='#31729C')

    return fig, fig_line

# Callback para o grafico de barras empilhado e pizza das despesas
@callback(
    Output('barras_resultado', 'figure'),
    Output('pie_despesas', 'figure'),
    Input('store_ano', 'data')
)
# Função para gráfico de barras e pie
def bar_pie_graph(ano):
    # Obtendo os Data Frames
    df_vendas, df_despesas = carregar_dados() # Obtendo os dados da tabela

    # Tratando Data Frame das vendas 
    # Selecionando os dados de acordo com o ano
    df_vendas = df_vendas[(df_vendas['Data da Venda'].dt.year == ano)]
    # Criando uma coluna nova contendo apenas o mês e o ano analisado.
    df_vendas['Data'] = df_vendas['Data da Venda'].apply(lambda x: x.strftime('%Y-%m'))
    
    # Tratando Data Frame das despesas 
    # Selecionando os dados de acordo com o ano
    df_despesas = df_despesas[(df_despesas['Data Pagamento'].dt.year == ano)]
    # Criando uma coluna nova contendo apenas o mês e o ano analisado.
    df_despesas['Data'] = df_despesas['Data Pagamento'].apply(lambda x: x.strftime('%Y-%m'))
   

    # Definindo o DataFrame do faturmaneto
    faturamento = df_vendas.groupby('Data').sum()
    faturamento.reset_index(inplace = True)
    faturamento.drop(columns=['Quantidade'], inplace = True)
    

    # Definindo o DataFrame das despesas
    despesas = df_despesas.groupby('Data').sum()
    despesas.reset_index(inplace = True)
    

    # Definindo o DataFrame do resultado 
    # Vamos agrupar os dados de faturamento e despesas
    resultado = pd.merge(faturamento, despesas, on='Data', how='outer', suffixes=('Faturamento', 'Despesas'))
    resultado.fillna(0, inplace = True) # Atribuindo valor 0 para os dados que estão 0 no data Frame
    # Agora calcularemos a diferença de acorod com a data entre a coluna faturamento e a coluna despesa. Para tal criei uma coluna chamada 'diferença' para armazenar os dados
    resultado['Diferença'] = resultado['Valor (R$)Faturamento'] - resultado['Valor (R$)Despesas']
    resultado['Valor (R$)Despesas'] = resultado['Valor (R$)Despesas']*-1
    resultado['Data'] = pd.to_datetime(resultado['Data'])
    resultado['Data'] = resultado['Data'].apply(lambda x: x.strftime('%b-%Y'))# Para tratar Data e mostrar apenas o mês abreviado
    


    # Definindo o gráfico de bar
    fig_bar = go.Figure()

    # Dados Faturamento
    fig_bar.add_trace(
        go.Bar(x = resultado['Data'], y = resultado['Valor (R$)Faturamento'], offset=0, name='Faturamento', marker_color='#84909C')
    )
    # Dados Despesas
    fig_bar.add_trace(
       go.Bar(x=resultado['Data'], y=resultado['Valor (R$)Despesas'], offset=0, name='Despesas', marker_color='#E74C3C') 
    )
    # Dados Diferença
    fig_bar.add_trace(
       go.Bar(x=resultado['Data'], y=resultado['Diferença'], offset=0, name='Resultado', marker_color='#31729C') 
    )

    # Editando o gráfico
    fig_bar.update_layout(

        xaxis_title='Data',
        yaxis_title='Volume (R$)', 

        template='plotly_white', # Estilo templete

        title={
            'text': 'Faturamento, gastos e resultado',
            'font': {'size': 24, 'family': 'Poppins, sans-serif'}
        },
       
    )
    # Editando o eixo x
    fig_bar.update_xaxes(showgrid=True, gridcolor='lightgray', tickangle=45, tickmode='linear', title_font=dict(size=16, family='Poppins, sans-serif'))
    # Editando o eixo y
    fig_bar.update_yaxes(showgrid=True, gridcolor='lightgray', title_font=dict(size=16, family = 'Poppins, sans-serif'))

    fig_pie = px.pie()
    
    if len(df_despesas) > 0:

        # Criando o gráfico de despesas por departamento 
        fig_pie = px.sunburst(df_despesas, path=['Departamento', 'Tipo de despesa'], 
                            color_continuous_scale='RdBu_r', values='Valor (R$)', 
                            color='Valor (R$)'
                    )
    
        # Editando o gráfico 
        fig_pie.update_layout(        
            title={
                'text': 'Tipos de gastos',
                'font': {'size': 22, 'family': 'Poppins, sans-serif'},
            },

            template='plotly_white', # Estilo templete

            margin=dict(t=50, l=70, r=80, b=60),

            legend=dict(
                font=dict(
                    family='Poppins, sans-serif',
                    size=10,
                ),
            )
            
        )


    return fig_bar, fig_pie

@callback(
    Output('dia', 'children'),
    Output('hora', 'children'),
    Input('dia_hora', 'n_intervals')
)
def update_dia_hora(interval):
    if interval:
        data_atual = dt.today().strftime("%d/%m/%Y")
        hora_atual = datetime.now().strftime("%H:%M")
        return data_atual, hora_atual
    else:
        return '', ''

        
# Callback para atualizar as tasks e definir a data de entrega   
@callback(
    Output('lista-ToDo', 'children'),
    Output('calendario_data', 'children'),
    Output('input-ToDo', 'value'),
    Output('store_ToDotask', 'data'),
    Output('add-task', 'n_clicks'),
    Output('calendario', 'n_clicks'),
    Input({'type': 'delete-task', 'index': ALL}, 'n_clicks'),
    Input('add-task', 'n_clicks'),
    Input('calendario', 'n_clicks'),
    Input('store_ToDotask', 'data'),
    Input('dia_hora', 'n_intervals'),
    Input('lista-ToDo', 'children'),
    State('input-ToDo', 'value'),
    State('data_ToDo', 'date'),
    State('lista-ToDo', 'children'),   

)
def update_todolist(delete, n_task, n_calender, store_children, interval, lista_todo, input, data, children):
    
    # Condição para zerar n_task e n_calender caso já terem sido acionado anteriormente.
    if not children:
        
        children = store_children

    if store_children is None:
        
        children = []
    else:
       
        store_children = children

    #fig, _ = pie_ToDo(children)

    # Obtenha o id do ano selecionado no filtro-ano
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
 
    # Condição para apagar
    if triggered_id != 'add-task' and triggered_id != 'calendario' and triggered_id != '' and triggered_id != 'dia_hora':
        
        input_id = json.loads(triggered_id) #Neste caso retorna a posição em que o botao delete foi assionado.
        index = input_id['index'] # COletando o index do delete acionado

        children = [
            chart
            for chart in children    
            if "'index': " + str(index) not in str(chart)
        ]


    else:
       
        if data is not None:
           
            if n_task and input and data:
                
                #Ajustando a data:
                data_ajustada = datetime.strptime(data, '%Y-%m-%d')
                data_ajustada = data_ajustada.strftime('%d/%m/%Y')
                    
                new_children = children + [
                    html.Div([
                        html.Div([
                            dbc.Checkbox(id={'type': 'checkbox-task', 'index': len(children)}, className='mr-2', style={'margin-top':'3px'}),

                            html.Li(id = {'type': 'texto-task', 'index': len(children)}, children = [input], 
                                    style={'font-family': fonte, 'font-size':'18px', 'list-style-type': 'none', 'width': '100%', 'margin-left':'5px'}),

                            html.I(id = {'type': 'status_task', 'index': len(children)}, className = "bi bi-record-fill text-warning", style={'width':'10%', 'font-size':'20px', 'margin-top':'12px'}),

                            html.Div([
                                dbc.Button(id = {'type': 'delete-task', 'index': len(children)}, className="bi bi-x-lg", outline = True, style={'margin-top':'3px', 'margin-right':'4px'})
                            ]),

                        ],
                        style={'display': 'flex', 'align-items': 'center'}
                        ),
                        html.Div([
                            html.H4(id = {'type': 'data_task', 'index': len(children)}, children=['\xa0'*11, data_ajustada], style={'font-family': fonte, 'font-size':'12px', 'width': '90%'}),
                            
                        ], style = {'width':'100%', 'display':'flex'}),
                         
                        html.Hr()
                    ])
                    ]
                n_task=None
                return [new_children,
                        html.Div(id='data_ToDo', children=[''], hidden = True), #escondido
                        '',
                        new_children,
                        n_task,
                        dash.no_update
                        ]
        
        elif n_calender:
            data_picker=dcc.DatePickerSingle(
                id='data_ToDo',
                min_date_allowed=dt(1930, 1, 1),
                max_date_allowed=dt(dt.today().year, 12, 31),
                initial_visible_month=dt.today(),
                display_format='DD/MM/Y',
                placeholder='Prazo task',
                show_outside_days = False, #o calendário pega apenas os dias daquele mês
                style = {'height':'0px', 'width':'0px', 'font-family': fonte, 'z-index':'999'},
                )
            
            n_calender=None
            return [dash.no_update, data_picker, dash.no_update, dash.no_update, dash.no_update, n_calender]


        #return [children, dash.no_update, dash.no_update, children, fig] # retorna sem atualizar se a data não foi selecionada
    
    return [children, dash.no_update, dash.no_update, children, dash.no_update, dash.no_update]


# Callback para atualizar o estilo do texto quando o usuário marcar o checkbox
@callback(
    Output({'type': 'texto-task', 'index': MATCH}, 'style'),
    Output({'type': 'status_task', 'index': MATCH}, 'className'),
    Input({'type': 'checkbox-task', 'index': MATCH}, 'value'),
    Input('store_ToDotask', 'data'),
    State({'type': 'data_task', 'index': MATCH}, 'children'),
)
def update_task_style(checked, children, data):
    
    # Extrai a data da tarefa a partir do objeto data
    data_ajustada = datetime.strptime(data[1], '%d/%m/%Y').date()
    data_atual = datetime.strptime(dt.today().strftime("%d/%m/%Y"), '%d/%m/%Y').date()

    if checked:
        texto = {'margin-left':'5px', 'text-decoration': 'line-through', 'color': '#6c757d', 'font-family': fonte, 'font-size':'18px', 'list-style-type': 'none', 'width': '100%'}
        status = "bi bi-record-fill text-success"


    else:
        texto = {'margin-left':'5px', 'text-decoration': 'none', 'color': 'black', 'font-family': fonte, 'font-size':'18px', 'list-style-type':'none', 'width': '100%'}
        status = "bi bi-record-fill text-warning"
        if data_ajustada < data_atual:
            status = "bi bi-record-fill text-danger"

    return texto, status  

# Callback para gerar o gráfico de acompanhamento do list to do 
@callback(
    Output('grafico-ToDo', 'figure'),
    Output('atraso', 'data'),
    Input('lista-ToDo', 'children'),
    State('lista-ToDo', 'children')
)
def atualizar_grafico(_, children):
    # Chamar a função pie_ToDo para atualizar o gráfico de acordo com os dados das tarefas
    fig, atraso = pie_ToDo(children)

    return fig, atraso


# Callback para enviar o e-mail
@callback(
    Output('inicio', 'className'),
    Output('ultimo_envio', 'data'),
    Output('tamanho_task', 'data'),
    Input('tempo_email', 'n_intervals'),
    State({'type': 'data_task', 'index': ALL}, 'children'),
    State('ultimo_envio', 'data'),
    State('atraso', 'data'),
    State('tamanho_task', 'data')
)
def enviar_email(_, data, ultimo_envio, atraso, tamanho_passado):

    if tamanho_passado is None:
        tamanho_passado=0
        return dash.no_update, dash.no_update, tamanho_passado 

    if ultimo_envio is None:
        ultimo_envio = dt.today()
        return dash.no_update, ultimo_envio, dash.no_update 

    if (datetime.strptime(ultimo_envio, '%Y-%m-%d').date() != data_atual) or (int(atraso) != int(tamanho_passado)):

        if atraso != 0:
            
            ultimo_envio = dt.today()
            tamanho_passado = atraso
            enviar_alerta('Atividade atrasada',
               f'Este é um lembrete amigável de que você possui {atraso} tarefas em atraso no StartChart. '
               f'Por favor, verifique as tarefas pendentes e conclua-as assim que possível. '
               f'\nLembre-se de que as tarefas em atraso podem afetar o desempenho geral da empresa.'
               f'\n'
               f'\nCordialmente,'
               f'\nStartChart',
               'reiskayron@gmail.com') 
            
        return dash.no_update, ultimo_envio, tamanho_passado 



    return dash.no_update, dash.no_update, dash.no_update
