from nicegui import ui
from db import initialize_db
from pages.main import main_page
from pages.fields import fields_page
from pages.map import map_page

initialize_db()

@ui.page('/')
def _():
    main_page()

@ui.page('/fields')
def _():
    fields_page()

@ui.page('/map')
def _(action: str = None, fields: str = None, field_id: str = None):
    map_page(action, fields, field_id)

ui.run()
