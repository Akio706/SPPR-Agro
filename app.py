from nicegui import app, ui
from db import initialize_db, Base, engine

# Эта строка обязательно должна быть до ui.run()
app.add_static_files('/static', 'static')

from pages.main import main_page
from pages.fields import fields_page
from pages.map import map_page
from pages.yields import show_yield_page, field_climate_page
from pages.climat import climat_page

Base.metadata.create_all(bind=engine)

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

@ui.page('/yields')
def _(field_id: int = 0):
    show_yield_page(field_id)

@ui.page('/climat')
def _():
    climat_page()

@ui.page('/field_climate')
def _(field_id: int = 0):
    field_climate_page(field_id)

ui.run()