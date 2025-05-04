from nicegui import app, ui
import plotly.express as px
import pandas as pd
import plotly.graph_objs as go
import json
from dash import html
from table.table import create_card
from calculation.calculation import calculation_of_harvest




ui.markdown('''This is **DSS**.''')
#--------------------табы-----------------------
with ui.tabs() as tabs:
    ui.tab('Home', icon='home')
    ui.tab('Choose region', icon='map')
    ui.tab('climatic data', icon='calendar_today')
    ui.tab('description of varieties', icon='info')
    ui.tab('projected harvest', icon='calculate')
    
# ---------------------наполнение табов-------------


with ui.tab_panels(tabs, value='home'):
 
# ------------нутрянка хома-------------

    # with ui.tab_panel('Home'):
    #     ui.label('This is the first tab')

    #     ui.button('Click me!', on_click=lambda: ui.notify(f'You clicked me!'))


# --------------нутрянка карты-----------

    # with ui.tab_panel('Choose region'):
    #     pass
    # with ui.tab_panel('climatic data'):
    #     pass


    with ui.tab_panel('projected harvest'):
        calculation_of_harvest()
        



    with ui.tab_panel('description of varieties'):
        with ui.card().tight() as card:
            create_card()



ui.run()