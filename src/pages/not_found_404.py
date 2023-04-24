import dash

dash.register_page(__name__, path = "/404")

from dash import html

# Mensagem de página não encontrada.
layout = html.H1("Erro 404")
