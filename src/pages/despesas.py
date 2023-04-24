import dash
import dash_extensions as de

from dash import Dash, dcc, html, Input, Output, State, dash_table, MATCH, ALL, callback, no_update
from dash.dash_table.Format import Format
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px

import pandas as pd
import numpy as np
import base64
import datetime
import io
import plotly.io as pio
import json

import pymongo
from pymongo import MongoClient

# Registra como uma página de navegação
# assim o app.py pode entender como página de navegação
dash.register_page(__name__)


# Obtendo animações
url = "https://assets4.lottiefiles.com/packages/lf20_N7k36k.json" #Animação de delete
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYmid slice'))

# Importação das fontes
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,700;1,400&display=swap']
# Estilo da fonte que será utilizada
fonte = {'fontFamily': 'Poppins, sans-serif'}

# Cor gráfico parcial do callback - dcc.Graph()
cor = {
    'background': 'white',
}



# Definir a mensagem de erro caso o usuário faça upload de uma planilha
#fora do modelo esperado
mensagem_erro = "Erro: as colunas da planilha não correspondem às esperadas. " \
                "Você pode fazer o download do modelo correto clicando em Download Modelo logo abaixo."
# Criar o componente ConfirmDialog para o pop-up de erro
popup_erro = dcc.ConfirmDialog(
    id='popup_erro-despesas',
    message=mensagem_erro,
    displayed=False
)


# Criando o banco de dados não relacional como MongoDB
# Conectando com o servidor local
client = MongoClient("mongodb+srv://tcc_122051:tnPQdZLXfyi3hMMw@tcc-122051.sy9tzlz.mongodb.net/test")

# Criando database do projeto
database = client['dashboardstartup']

# Criando um grupo de documentos no MongoDB
doc_despesas = database['baseDespesas']


layout = html.Div([
    html.Div([
        html.H2(' '),
    ], style= {'width': '92%','display': 'inline-block','margin-top': '1vh',}),
    
    html.Div(
        id= 'inicio', children = [
        dbc.Button("Dúvida?", id="abrir", color = 'warning', outline = True, n_clicks=0,
                   style={'margin-top':'10px'}),
        dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle("Dúvida", style={'color': 'white', 'fontWeight': 'bold'}),
            ], style={'background-color': '#2C3E50'}
            ),
            dbc.ModalBody("Para começar, clique em 'Selecionar Arquivo' ou arraste um arquivo para a área 'Arraste e Solte' abaixo. Em seguida, uma tabela será exibida, permitindo que você a filtre e organize conforme necessário. Depois, clique em 'Novo Gráfico' para criar um gráfico interativo para o seu dashboard. Selecione o tipo de gráfico e escolha os dados para os eixos X e Y",
                style={'font-family': fonte, 'color': 'black', 'text-align': 'justify', 'text-justify': 'inter-word'}),
            dbc.ModalFooter(
                dbc.Button("Fechar", id="fechar", color='danger', n_clicks=0),
                style={'background-color': 'white'}
            ),
        ], id="pop-up-despesas", is_open=False
        )
        ], style= {'width': '8%','display': 'inline-block', 'margin-top': '1vh',}
    ),

    # Upload de arquivo para análise
    dcc.Upload(
        id='upload-dados',
        

        children = html.Div([
            
            html.A(className = "bi bi-cloud-arrow-up-fill",
                   style={'color':'black', 'font-size': '25px', 'vertical-align': 'middle'}),

            html.A('\xa0 \xa0 Arraste e Solte ou Selecione um Arquivo',
                   #className = "bi bi-cloud-arrow-up-fill",
                   style={'color':'black', 'font-size': '18px','text-decoration':'None', 'vertical-align': 'middle'}),
            
            ]),
        
        # Definindo as dimensões do botão
        style={
            'width': '90%',
            'height': '7vh',
            'left': '5%',
            'lineHeight': '6vh',
            'borderWidth': '1px',
            'borderStyle': 'ridge',
            'box-shadow': '2px 1px 5px 2px rgba(0, 0, 0, 0.2)',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '0.01vh',
            'color': 'black',
            'margin-top': '20px',
            'font-weight': 'bold',  
        },
        # Permite upload de múltiplos arquivos
        multiple=True,
        
    ),

    html.Div([
        html.P(''),
    ]),

    # Div para o botão de criar gráficos e download modelo
    html.Div([
    # Gráfico
    html.Div([
        html.P(''),
        dbc.Button(
        " \xa0 Novo Gráfico", color="primary", id = "novo_grafico",
        outline = False, n_clicks=0, className="bi bi-bar-chart-fill")
    ], style = {'width': '87%', 'display': 'inline-block'}),
    # Download Modelo
    html.Div([
        # Botão para download do modelo CSV.
        dbc.Row([
        dbc.Button(
        " \xa0 Download Modelo", color="primary", id = "click-despesas-modelo-csv",
        outline = False, className="bi bi-download"),
        dcc.Download(id="despesas-csv"),
        ],
        # Dimensões do botão
            style={
                'width':'27vh',
                'height':'3vh',
            }
        )
    ], style = {'width': '13%', 'display': 'inline-block'})
    ]),

    html.P(' '),

    # Div para aceitar os gráficos 
    html.Div(id='estrutura-despesas', children=[], style={'background-color': 'white', 'border-color': 'gray',
                                                 'border-style': 'solid', 'border-radius': '10px'}),
    
    
    # Div para receber a tabela dos dados que foram carregados
  
    html.Div(id='output-data-upload-despesas', style={'background-color': 'white'}),

    

    html.P(""),
    # Botão Salvar, Adicionar Linha e Gerar Base
    dbc.Row([
    dbc.Button(" \xa0 Salvar Alterações", color="success", id = "salvar-baseDespesas",
        outline = False, className="bi bi-check2-square"),
    ], style = {'width':'27vh', 'height':'3vh', 'margin-left':'0.1%', 'display': 'inline-block'}),
    # Botão para adicionar linhas no banco de dados
    dbc.Row([
    dbc.Button(" \xa0 Adicionar Linha", color="info", id = "adicionarLinha-baseDespesas",
        outline = False, className="bi bi-plus-square"),
    ], style={'width':'27vh', 'height':'3vh', 'margin-left':'2%', 'display': 'inline-block'}),
    # Botão para download da tabela:
    dbc.Row([
    dbc.Button(" \xa0 Baixar Tabela", color="warning", id = "gerar-tabela",
        outline = False, className="bi bi-download"),
    dcc.Download(id='download-tabela-despesas')
    ], style={'width':'27vh', 'height':'3vh', 'margin-left':'2%', 'display': 'inline-block'}),
    

    # Botão para adicionar linhas no banco de dados
    dbc.Row([
        dbc.Button(" \xa0 Apagar tabela", id="abrir-apagar", color = 'danger', outline = False,
                   n_clicks = 0, className="bi bi-trash3-fill"),
        dbc.Modal([
            dbc.ModalHeader([
                html.Div(de.Lottie(options=options, width="100%", height="100%", url = url, speed=0.8)),
                dbc.ModalTitle("Você tem certeza?", style={'color': 'black', 'fontWeight': 'bold', 'margin-top': '1vh'}),
                
            ],  className='d-flex flex-column justify-content-center align-items-center',
                close_button=False,
                style={'background-color': 'white'}
            ),

            dbc.ModalBody(
                "Você tem certeza de que deseja excluir os dados abaixo? Por favor, esteja ciente de que a exclusão será permanente e irreversível, o que pode afetar significativamente os resultados já apresentados no dashboard.",
                style={'color':'black', 'text-align': 'justify', 'text-justify': 'inter-word'}
            ),

            dbc.ModalFooter([
                # Botão de cancelar
                dbc.Button('Cancelar', id = 'cancelar-apagar', color = 'info', outline = False, n_clicks = 0),
                
                # Botão para confimar a exclusão da tabela
                dbc.Button('Apagar mesmo assim', id = 'apagar-baseDespesas', color = 'danger', outline = False),
            ])
        ], id="pop-up-apagar-despesas", is_open=False
        ),
    ], style={'width':'27vh', 'height':'3vh', 'margin-left':'44%', 'display': 'inline-block'}
    ),

    #Div para exibir a mensagem de erro para o usuário 
    html.Div(
        popup_erro,
    ),
    

    # Ativa uma vez por dia ou quando a página é recarregada
    dcc.Interval(id= 'mongoDB', interval = 86400000, n_intervals = 0),

    html.Div(id='espaço-despesas', children=[]),
    html.Div(id='espaço2', children=[])
], 
),

def apagar_Mango(n):
    record = {
    "Tipo de despesa": "",    
    "Descrição": "",
    "Valor (R$)": "",
    "Data Pagamento": "",
    "Data Vencimento": "",
    "Departamento": "",
    }

    if n is not None:
        doc_despesas.delete_many({})
        doc_despesas.insert_one(record)
    return ''

def upload(contents, filename, date):
    if date is None:
        return PreventUpdate
    
    else:
        content_type, content_string = contents.split(',')

        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
            # Assume that the user uploaded a CSV file
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                dff = df.to_dict('records')
            elif 'xls' in filename:
            # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
                dff = df.to_dict('records')


        except Exception as e:
            
            return html.Div([
                'Erro - Tente novamente'
            ])    
      
        return df


# Callback para postar o arquivo que foi carregado.
@callback(  
    Output("output-data-upload-despesas", "children"),
    Output('popup_erro-despesas', 'displayed'),
    Input('upload-dados', 'contents'),
    Input('mongoDB', 'n_intervals'),
    Input('apagar-baseDespesas', 'n_clicks'),
    State('upload-dados', 'filename'),
    State('upload-dados', 'last_modified'), 
    State('popup_erro-despesas', 'displayed'),
)
# Agora podemos mostrar o conteúdo que foi carregado 
def output(conteudo, mongo, n, nome, datas, popup_displayed):

    # Iniciando o callback com a condição pop-up erro fechada
    popup_erro.displayed = False

    # Acessando o banco de dados MongoDB:
    df = pd.DataFrame(list(doc_despesas.find()))
    df = df.iloc[:, 1:]
    
    if conteudo is None:
        result = df

    else:
        children = [
            upload(x, y, z) for x, y, z in
            zip(conteudo, nome, datas)
        ]
        result = pd.DataFrame(next(iter(children), None))
        result = result.append(df)
    
    if n is not None:
        df = apagar_Mango(n)

        result = pd.DataFrame(list(doc_despesas.find()))
        result = result.iloc[:, 1:]
    
    
    columns_aux_despesa = [
        "Tipo de despesa",
        "Descrição",
        "Valor (R$)",
        "Data Pagamento",
        "Data Vencimento",
        "Departamento",
    ]


    # Verificando se todas as colunas estão presentes no data frame
    if list(result.columns) != columns_aux_despesa:
        
        df = apagar_Mango(n=True)

        result = pd.DataFrame(list(doc_despesas.find()))
        result = result.iloc[:, 1:]  

        if not popup_displayed: #Se o popup_erro.displayed = False
            popup_erro.displayed = True
        
       



    columns= [{'name': i, 'id': i} for i in result.columns]
    #[{'name': 'Vendedor', 'id': 'Vendedor'}, {'name': 'Data da Venda', 'id': 'Data da Venda'}, 
    # {'name': 'Cliente', 'id': 'Cliente'}, {'name': 'Valor (R$)', 'id': 'Valor (R$)'}, 
    # {'name': 'Cod_Produto', 'id': 'Cod_Produto'}, {'name': 'Quantidade', 'id': 'Quantidade'}, 
    # {'name': 'UF', 'id': 'UF'}, {'name': 'Forma_Pagamento', 'id': 'Forma_Pagamento'}]
    # Criando um dicionário com os tipos de input para cada coluna desejada
    
    input_types = {
    "Tipo de despesa": "text",
    "Descrição": "text",
    "Valor (R$)": "numeric",
    "Data Pagamento": "datetime",
    "Data Vencimento": "datetime",
    "Departamento": "text",  
    }

    # Percorra a lista de colunas e adicione o tipo de input correspondente, se existir no dicionário de mapeamento
    for col in columns:
        if col['name'] in input_types:
            col['type'] = input_types[col['name']]

    
    
    return[
        dash_table.DataTable(result.to_dict('records'),
                              
            columns= columns,

            id = 'tabela-despesas', 

            style_cell={'padding': '5px', 'textAlign': 'center'},

            style_header={'color': 'white', 'fontWeight': 'bold', 
                'background':'#2C3E50'
            },

            style_data={'color': 'rgb(37, 37, 37)', 
                'background':'white'
            },

            style_data_conditional=[
        
                {'if': {'row_index': 'odd'},'backgroundColor': '#e0eefc'},

            ],

            filter_options={
                'backgroundColor': 'rgba(66, 66, 66,0.4)',
                'color': 'white',
                'fontWeight': 'bold',
                'placeholder': 'Filtrar dados',
                "case": "sensitive"
            },
            style_as_list_view=True,
            sort_action="native",
            sort_mode="single",
            filter_action="native",
            editable = True,
            row_deletable=True,

            # Legenda para ao passar o mouse sobre a tabela
            tooltip={
                'Tipo de despesa': {
                    'value': 'Tipo de despesa',
                    'use_with': 'both' #Células e o header
                },        
                'Data Pagamento': {
                    'value': str('aaaa-mm-dd'),
                    'use_with': 'both' #Células e o header
                },
                'Data Vencimento': {
                    'value': str('aaaa-mm-dd'),
                    'use_with': 'both' #Células e o header
                },   
                'Valor (R$)': {
                    'value': 'Formato 000.00',
                    'use_with': 'both' # Somente nas células
                },
                'Departamento': {
                    'value': 'Departamento responsável',
                    'use_with': 'both'
                },         
                'Descrição': {
                    'value': 'Descrição da despesa',
                    'use_with': 'both'
                }               
            },

            css=[{
                'selector': '.dash-table-tooltip',
                'rule': 'background-color: white; color: black; text-align: center'
            }],

            page_size=20),
    
    ], popup_erro.displayed

    



# Adicionar nova linha na tabela:
@callback(
    Output('tabela-despesas', 'data'),
    Input('adicionarLinha-baseDespesas', 'n_clicks'),
    State('tabela-despesas', 'data'),
    State('tabela-despesas', 'columns')
)
def adicionar_linha(n, linhas, columns):
    if n is not None:
        linhas.append({c['id']: '' for c in columns})
    
    return linhas



# Salvar os dados atualizados no MongoDB
@callback(
    Output('espaço-despesas', 'children'),
    Input('salvar-baseDespesas', 'n_clicks'),
    State('tabela-despesas', 'data'),
    prevent_initial_call=True
)
def salvar_Mango(n, dados):
    if n is not None:
        df = pd.DataFrame(dados)
        doc_despesas.delete_many({})
        doc_despesas.insert_many(df.to_dict('records'))
    return ''



# Gerar excel da tabela
@callback(
    Output('download-tabela-despesas', 'data'),
    Input('gerar-tabela', 'n_clicks'),
    State('tabela-despesas', 'data'),
    prevent_initial_call=True
)
def download(n, dados):
    df = pd.DataFrame(dados)
    if n is not None:
        return dcc.send_data_frame(df.to_excel, "tabela_despesas.xlsx",
            sheet_name="Despesas", index = False)



# Callback para gerar as estruturas dos gráficos
@callback(
    Output('estrutura-despesas', 'children'),
    Input('novo_grafico', 'n_clicks'),
    Input({"type": "dynamic-delete", "index": ALL}, "n_clicks"),
    State('estrutura-despesas', 'children'),
    State('tabela-despesas', 'data')
)
# Função para gerar as estruturas dos gráficos
def estrutura_grafico(n_clicks, _, children, dados):
    df = pd.DataFrame(dados)
    #print(children)
    # triggered retorna uma lista de todas as propriedades de entrada que foram alteradas e causaram
    # a execução do retorno de chamada
    input_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0] # Retorna o id do componente que acionou o retorno de chamada
    # Exemplo de retorno: {"index":2,"type":"dynamic-delete"}
    #print(input_id)
    
    if "index" in input_id:

        delete_chart = json.loads(input_id)["index"] # Decodifica o objeto retornando o index. Esse valor de retorno de object_hook será usado em vez do dict
        # Neste caso retorna a posição em que o botao delete foi assionado.
        #print(delete_chart)
        children = [
            chart
            for chart in children    
            if "'index': " + str(delete_chart) not in str(chart)
        ]
        
    else:
        nova_div = html.Div(
            children=[
                #Botão de delete do gráfico:
                dbc.Button(
                    "X",
                    id={'type': 'dynamic-delete',
                        'index': n_clicks
                    },
                    n_clicks=0,
                    color="danger",
                    size='sm', outline = False,
                    style={"display": "block", 'margin-top':'3px', 'margin-left':'3px'},
                ),

                # Estrutura gráfico
                dcc.Graph(
                    id = {'type': 'grafico-dinamico-despesas',
                    'index': n_clicks
                    },
                    figure={
                        'layout': {
                        'plot_bgcolor': cor['background'],
                        'paper_bgcolor': cor['background'],
                        }    
                    },
                ),

                # Estrutura para os tipos de gráficos 
                dcc.RadioItems(
                    id = {'type': 'tipo-dinamico',
                        'index': n_clicks
                    },
                    options=[
                        {'label': '\xa0Barras \xa0\xa0','value':'bar'},
                        {'label': '\xa0Dispersão \xa0\xa0','value':'scatter'},
                        {'label': '\xa0Linha \xa0\xa0','value':'line'},
                        {'label': '\xa0Histograma \xa0\xa0','value':'histogram'},
                        {'label': '\xa0Pizza \xa0\xa0','value':'pie'},
                        {'label': '\xa0Box Plot \xa0\xa0','value':'box'}
                    ],
                    inline = True,
                    style = {'width': '100%', 'color': 'black', 'font-size': '15',
                            'padding': '15px', 'margin':'auto'},       
                    value = 'bar'

                ),
                # Estrutura eixo x
                dcc.Dropdown(
                    id = {'type': 'eixoX-dinamico',
                        'index': n_clicks
                    },
                    options=[{'label':x, 'value':x} for x in df.columns],
                    placeholder="Selecione eixo X",
                    optionHeight=30,
                    maxHeight=100,
                    style={'color':'black','fontWeight': 'bold', 'backgroundColor':'white'}
                ),
                # Estrutura eixo y
                dcc.Dropdown(
                    id = {'type': 'eixoY-dinamico',
                        'index': n_clicks
                    },
                    options=[{'label':y, 'value':y} for y in df.columns],
                    placeholder="Selecione eixo Y",
                    optionHeight=30,
                    maxHeight=100,
                    style={'color':'black', 'fontWeight': 'bold', 'backgroundColor':'white'}
                ),
            html.P(' ')
            ], 
            style={'width': '50%', 'display': 'inline-block'}
        )

        # Agrupando as estruturas criadas conforme cada ação do Callback (adicionar )
        children.append(nova_div)
    return children



# Callback para gerar os gráficos
@callback(
    Output({'type': 'grafico-dinamico-despesas', 'index': MATCH}, 'figure'),
    Input({'type': 'tipo-dinamico', 'index': MATCH}, 'value'),
    Input({'type': 'eixoX-dinamico', 'index': MATCH}, 'value'),
    Input({'type': 'eixoY-dinamico', 'index': MATCH}, 'value'),
    Input('tabela-despesas', 'data'),
    prevent_initial_call=True
)
# Função para gerar os gráficos
def gerar_grafico(tipo, eixoX, eixoY, dados):

    if tipo == 'bar':
        bar_fig = px.bar(dados, x = eixoX, y = eixoY, template="simple_white", 
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return bar_fig

    elif tipo == 'scatter':
        scatter_fig = px.scatter(dados, x = eixoX, y = eixoY, template="simple_white", 
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return scatter_fig

    elif tipo == 'line':
        line_fig = px.line(dados, x = eixoX, y = eixoY, template= 'simple_white',
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return line_fig

    elif tipo == 'histogram':
        histogram_fig = px.histogram(dados, x = eixoX, y = eixoY, template='simple_white',
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return histogram_fig

    elif tipo == 'pie':
        pie_fig = px.pie(dados, values = eixoX, names = eixoY, template= 'simple_white',
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return pie_fig

    elif tipo == 'box':
        box_fig = px.box(dados, x = eixoX, y = eixoY, template= 'simple_white',
        title='{} x {}'.format(eixoX,eixoY),
        color_discrete_sequence=px.colors.sequential.RdBu)
        return box_fig



# Callback para abrir e fechar o botão de dúvida
@callback(
    Output("pop-up-despesas", "is_open"),
    [Input("abrir", "n_clicks"), Input("fechar", "n_clicks")],
    State("pop-up-despesas", "is_open"),
)
def pop_up(abrir, fechar, estado):
    if abrir or fechar:
        return not estado
    return estado



# Callback do botão download
@callback(
    Output("despesas-csv", "data"),
    Input("click-despesas-modelo-csv", "n_clicks"),
    prevent_initial_call=True,
)
# Função Download do arquivo modelo vendas
def download(n_clicks):
    if n_clicks is not None:
        return dcc.send_data_frame(arquivo_modelo.to_excel, "modelo_despesas.xlsx",
            sheet_name="Modelo", index = False)


# Arquivo Modelo Vendas (Download)
arquivo_modelo = pd.DataFrame(columns=['Tipo de despesa', "Descrição", "Valor (R$)", "Data Pagamento",  "Data Vencimento", 
"Departamento"])


# Callback para abrir e fechar o botão de apagar tabela
@callback(
    Output("pop-up-apagar-despesas", "is_open"),
    [Input("abrir-apagar", "n_clicks"), 
     Input("cancelar-apagar", "n_clicks"),
     Input("apagar-baseDespesas", "n_clicks")],
    State("pop-up-apagar-despesas", "is_open"),
)
def pop_up(abrir, cancelar, confirmar, estado):
    if abrir or cancelar or confirmar:
        return not estado
    return estado