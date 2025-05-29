from nicegui import app, ui
from db import initialize_db, Base, engine
import geopandas as gpd
from starlette.responses import JSONResponse
from fastapi import Request

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

@app.get('/api/soil_geojson')
def soil_geojson(request: Request):
    min_lat = request.query_params.get('min_lat')
    min_lng = request.query_params.get('min_lng')
    max_lat = request.query_params.get('max_lat')
    max_lng = request.query_params.get('max_lng')
    gdf = gpd.read_file('soil_regions_full.gpkg')
    if all([min_lat, min_lng, max_lat, max_lng]):
        min_lat = float(min_lat)
        min_lng = float(min_lng)
        max_lat = float(max_lat)
        max_lng = float(max_lng)
        # Фильтрация по bbox (cx: lng, lat)
        gdf = gdf.cx[min_lng:max_lng, min_lat:max_lat]
    return JSONResponse(content=gdf.to_json())

ui.run()