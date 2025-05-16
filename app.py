from nicegui import app, ui
from monitoring import generate_fields_map, generate_ndvi_map, generate_dem_map
from flask import Flask, Response, jsonify
from advisory import get_field_advisory
from weather import get_weather_for_field

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

@app.route('/fields_map')
def fields_map():
    m = generate_fields_map('polygons.geojson')
    return m._repr_html_()

@app.route('/ndvi_map/<int:field_id>')
def ndvi_map(field_id):
    m = generate_ndvi_map('polygons.geojson', field_id)
    return m._repr_html_()

@app.route('/dem_map/<int:field_id>')
def dem_map(field_id):
    m = generate_dem_map('polygons.geojson', field_id)
    return m._repr_html_()

@app.route('/advisory/<int:field_id>')
def advisory(field_id):
    result = get_field_advisory('polygons.geojson', field_id)
    return jsonify(result)

@app.route('/weather/<int:field_id>')
def weather(field_id):
    result = get_weather_for_field('polygons.geojson', field_id)
    return jsonify(result)

ui.run()