from nicegui import app, ui

# Эта строка обязательно должна быть до ui.run()
app.add_static_files('/static', 'static')

# Ваш роутинг:
from pages.main import main_page
from pages.fields import fields_page
from pages.map import map_page
from pages.yields import yields_page
from pages.climat import climat_page

@ui.page('/')
def _():
    main_page()

@ui.page('/fields')
def _():
    fields_page()

@ui.page('/map')
def _(action: str = None, fields: str = None, field_id: str = None):
    map_page(action, fields, field_id)

@ui.page('/yields')
def _():
    yields_page()

@ui.page('/climat')
def _():
    climat_page()

ui.run()