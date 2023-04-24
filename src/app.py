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
    brand="Dashboard Financeiro",
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
    ], style={'background-color': '#EBECF0', 'height': 'auto', 'margin': '0', 'padding':'0', 'z-index': '-9999'},
    fluid=True),
])



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

