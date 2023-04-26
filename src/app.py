import dash
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import base64

import pymongo
from pymongo import MongoClient

aux = dbc.themes.FLATLY
app = Dash(__name__, use_pages=True, external_stylesheets=[aux, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

# Criando o banco de dados não relacional como MongoDB
# Conectando com o servidor local
local = MongoClient('mongodb+srv://tcc_122051:tnPQdZLXfyi3hMMw@tcc-122051.sy9tzlz.mongodb.net/test')

# Criando database do projeto
database = local['dashboard_startup']

# Criando um grupo de documentos no MongoDB
doc_venda = database.baseVendas


# Importação das fontes
external_stylesheets = ['https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,600;0,700;1,400&display=swap']
# Estilo da fonte que será utilizada
fonte = {'fontFamily': 'Poppins, sans-serif'}



pages = [
    page for page in dash.page_registry.values()
    if page["module"] != "pages.not_found_404"
]



# Vamos importar a logo
#with open('C:/Users/KayronIdarilioRibeir/OneDrive - STARTPAY/Documentos/Projeto/2023.04.23/src/logo.png', 'rb') as f:
#'C:/Users/KayronIdarilioRibeir/OneDrive - STARTPAY/Documentos/2023.04.02/logo.png', 'rb') as f:
#C:/Users/kayro/OneDrive/Documentos/Projeto - TCC2/2023.03.31/logo.png', 'rb') as f:
#'C:/Users/KayronIdarilioRibeir/OneDrive - STARTPAY/Documentos/25.03.2023/logo.png', 'rb') as f:
#C:/Users/kayro/Projeto/pages/logo.png
    #logo = base64.b64encode(f.read()).decode()
#html.Img(src='data:image/png;base64,{}'.format(logo), 
#                         style={'height':'60px'})

# Definindo as paginas de navegação
navbar = dbc.NavbarSimple([

    html.Div([
        dbc.NavItem()
    ], style={'width':'100%'}),
    dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem(page["name"], href=page["path"])
            for page in pages
            if page["module"] != "pages.not_found_404"
        ],
        nav=True,
        id="dropdown-menu",
        style = {'margin': '0.8rem'}
    ),
],
    brand = html.A(html.Img(src='/assets/logo-startchart.svg', style={'margin-left':'50px', 'height': '80px', 'width': '100px', 'transform': 'scale(2.0)'})),
    color='primary',
    dark=True,
    sticky='top',
    style={'margin': '0', 'padding':'0', 'widht': '100vh'},
    fluid=True
)


app.layout = html.Div([
    dbc.Container([
        navbar, 

        dcc.Location(id="url", refresh= False),

        dash.page_container, 

    ], style={'background-color': '#EBECF0', 'height': '100%', 'margin': '0', 'padding':'0', 'z-index': '-9999', 'margin-bottom': '50px'},
    fluid=True),

        html.Footer([
            # Imagens
            html.Div([
    
                # Meu logo
                html.A(html.Img(src='/assets/logo-startchart.svg', 
                                style={'margin-left':'80px', 'height': '80px', 'width': '100px', 'transform': 'scale(2.0)',
                                       'margin-top':'15px'})
                ),
                
                html.Div([
                    # Link Github
                    html.A(href = 'https://github.com/Barao23/dashboard-startup.git', className="bi bi-github",
                        style={'color': 'white', 'transform': 'scale(2.5)', 'margin-right': '50px'}
                    ),
                    
                    # Link Linkedin
                    html.A(href = 'https://www.linkedin.com/in/kayron-reis-558b29170/', className="bi bi-linkedin",
                        style={'color': 'white', 'transform': 'scale(2.5)', 'margin-left': '50px'}
                    ),
                ], style={'margin-top':'65px', 'height':'auto', 'display':'flex'}),
    
                
                # Logo UNIFESP
                html.A(html.Img(src='/assets/logo.png', 
                                style={'height': '60px', 'width': '100px', 'transform': 'scale(1.2)',
                                       'margin-top':'30px', 'margin-right':'50px'})
                ),

            ], style = {'display':'flex', 'justify-content':'space-between'}
            ),
            # Agradecimentos
            html.Div([
                html.P("Gostaria de expressar minha sincera gratidão a todos que me" 
                       " apoiaram durante essa jornada. Não teria chegado aqui sem o amor,"
                       " o encorajamento e o apoio de minha família, amigos e mentores. Obrigado!",
                    style={'width': '40%', 'text-align': 'center', 'margin-top':'10px',
                           'fontFamily': fonte, 'color':'#DDDDDD', 'font-weight':'bold'}
                ),

            ], style = {'display':'flex', 'justify-content':'center', 'margin-bottom':'15px'}
            ),

            html.Hr(style={'margin':'0'}),

            html.P("© 2023 - Kayron Reis 122051", 
                   style={'fontFamily': fonte, 'margin-top':'15px',
                          'display':'flex', 'justify-content':'center'}),

        ], style={'background-color': '#31485A', 'height': '17rem', 'margin': '0', 'padding':'0', 'z-index': '-9999'}
        )

], style = {'background-color': '#EBECF0', 'height': 'auto', 'margin': '0 '})



@app.callback(
    Output("dropdown-menu", "label"),
    Input("url", "pathname")
)
def label_dropdown(pathname):
    page_name = ""
    for page in pages:
        if page["path"] == pathname:
            page_name = page["name"]
            break
    return page_name


if __name__ == "__main__":
    app.run_server(debug=True)

