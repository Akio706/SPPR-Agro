from nicegui import ui
from db import Session, Field
import requests
import json
from utils import get_arcgis_soil_params
import csv
import geopandas as gpd
from shapely.geometry import Polygon, shape
from shapely.ops import unary_union
from datetime import datetime
import openpyxl
from openpyxl import Workbook

def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,wind_speed_10m&forecast_days=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temps = data['hourly']['temperature_2m']
        precs = data['hourly']['precipitation']
        winds = data['hourly']['wind_speed_10m']
        avg_temp = sum(temps) / len(temps) if temps else None
        avg_prec = sum(precs) / len(precs) if precs else None
        avg_wind = sum(winds) / len(winds) if winds else None
        return avg_temp, avg_prec, avg_wind
    return None, None, None

def dodonov_formula(area, temp, prec, wind):
    # Урожай = площадь * (0.8*темп + 0.5*осадки - 0.3*ветер)
    return area * (0.8*temp + 0.5*prec - 0.3*wind)

def monteith_formula(area, temp, prec, rad=15):
    # FAO/Монтей: Урожай = площадь * рад * (темп/25) * (осадки/100)
    return area * rad * (temp/25) * (prec/100)

def fao_simple(area, temp, prec):
    # FAO простая: Урожай = площадь * (темп + осадки/10)
    return area * (temp + prec/10)

def show_yield_page(field_id: int):
    session = Session()
    field = session.query(Field).filter(Field.id == field_id).first()
    session.close()
    if not field:
        ui.notify('Поле не найдено', color='negative')
        return
    coords = json.loads(field.coordinates)
    coords_latlng = get_field_coords(coords)
    if not coords_latlng or len(coords_latlng) < 3:
        ui.notify('Нет координат у поля', color='negative')
        return
    poly = Polygon([(p[1], p[0]) for p in coords_latlng])
    gdf = gpd.read_file('soil_regions_full.gpkg')
    intersected = gdf[gdf.geometry.intersects(poly)]
    all_soil_types = sorted(set(x for x in gdf['soil_legend_Descript'].dropna().unique().tolist() if x and x.strip()))
    if not intersected.empty:
        soil_type_default = intersected.iloc[0]['soil_legend_Descript']
    else:
        soil_type_default = all_soil_types[0] if all_soil_types else ''
    if field.soil_type and field.soil_type in all_soil_types:
        soil_type_default = field.soil_type
    if soil_type_default and soil_type_default not in all_soil_types:
        all_soil_types.insert(0, soil_type_default)
    soil_type_state = {'value': soil_type_default}
    variety_options = ['Аннушка', 'Гордея', 'Луч', 'Золотая']
    sort_state = {'value': field.group or variety_options[0]}

    def on_soil_change(e):
        soil_type_state['value'] = e.value
    def on_sort_change(e):
        sort_state['value'] = e.value

    area_ha = poly.area * 111 * 111 if poly else 0  # Грубо для EPSG:4326

    with ui.row().classes('w-full'):
        with ui.column().classes('w-2/3'):
            m = ui.leaflet(center=[sum(p[0] for p in coords_latlng) / len(coords_latlng), sum(p[1] for p in coords_latlng) / len(coords_latlng)], zoom=13).classes('h-96 w-full')
            if coords_latlng:
                m.generic_layer(name='polygon', args=[coords_latlng, {'color': 'red', 'weight': 2}])
        with ui.column().classes('w-1/3'):
            ui.label('Информация о поле').classes('text-h6')
            table_data = [
                {'Параметр': 'Название поля', 'Значение': field.name},
                {'Параметр': 'Площадь (га)', 'Значение': f'{area_ha:.2f}'},
                {'Параметр': 'Тип почвы', 'Значение': soil_type_state['value']},
            ]
            ui.table(columns=[{'name': 'Параметр', 'label': 'Параметр', 'field': 'Параметр'}, {'name': 'Значение', 'label': 'Значение', 'field': 'Значение'}], rows=table_data).classes('mb-4')
            ui.select(all_soil_types, value=soil_type_state['value'], label='Тип почвы', on_change=on_soil_change).classes('q-mb-md')
            ui.select(variety_options, value=sort_state['value'], label='Сорт', on_change=on_sort_change).classes('q-mb-md')
            def save_changes():
                session = Session()
                f = session.query(Field).filter(Field.id == field_id).first()
                if f:
                    f.soil_type = soil_type_state['value']
                    f.group = sort_state['value']
                    f.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()
                    ui.notify('Данные сохранены', color='positive')
                session.close()
            ui.button('Сохранить', on_click=save_changes).props('color=primary').classes('mt-2')
    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

def normalize_coords(coords):
    if not coords or not isinstance(coords, list):
        return []
    if isinstance(coords[0], list):
        return [item for sub in coords for item in normalize_coords(sub)]
    if isinstance(coords[0], dict):
        return [[float(p['lat']), float(p['lng'])] for p in coords if 'lat' in p and 'lng' in p]
    if isinstance(coords[0], (tuple, list)) and len(coords[0]) == 2:
        return [[float(p[0]), float(p[1])] for p in coords]
    return []

def get_field_coords(coords):
    # Если GeoJSON Feature
    if isinstance(coords, dict) and 'geometry' in coords:
        coords_arr = coords['geometry']['coordinates'][0]
        return [[c[1], c[0]] for c in coords_arr]
    # Если список списков (обычно [[{'lat':..., 'lng':...}, ...]])
    if isinstance(coords, list) and len(coords) > 0:
        if isinstance(coords[0], list):
            inner = coords[0]
            # [{'lat':..., 'lng':...}, ...]
            if len(inner) > 0 and isinstance(inner[0], dict):
                return [[float(p['lat']), float(p['lng'])] for p in inner]
            # [[lat, lng], ...]
            if len(inner) > 0 and isinstance(inner[0], (list, tuple)) and len(inner[0]) == 2:
                return [[float(p[0]), float(p[1])] for p in inner]
        # [{'lat':..., 'lng':...}, ...]
        if isinstance(coords[0], dict):
            return [[float(p['lat']), float(p['lng'])] for p in coords]
        # [[lat, lng], ...]
        if isinstance(coords[0], (list, tuple)) and len(coords[0]) == 2:
            return [[float(p[0]), float(p[1])] for p in coords]
    return []

def field_climate_page(field_id: int):
    session = Session()
    field = session.query(Field).filter(Field.id == field_id).first()
    session.close()
    if not field:
        ui.notify('Поле не найдено', color='negative')
        return
    coords = json.loads(field.coordinates)
    coords_latlng = get_field_coords(coords)
    if not coords_latlng or len(coords_latlng) < 3:
        ui.notify('Недостаточно точек для построения полигона', color='negative')
        return
    lat_center = sum(p[0] for p in coords_latlng) / len(coords_latlng)
    lng_center = sum(p[1] for p in coords_latlng) / len(coords_latlng)
    poly = Polygon([(p[1], p[0]) for p in coords_latlng])

    gdf = gpd.read_file('soil_regions_full.gpkg')
    intersected = gdf[gdf.geometry.intersects(poly)] if poly else gdf.iloc[[]]
    all_soil_types = sorted(set(x for x in gdf['soil_legend_Descript'].dropna().unique().tolist() if x and x.strip()))
    if not intersected.empty:
        soil_type_default = intersected.iloc[0]['soil_legend_Descript']
    else:
        soil_type_default = all_soil_types[0] if all_soil_types else ''
    if field.soil_type and field.soil_type in all_soil_types:
        soil_type_default = field.soil_type
    if soil_type_default and soil_type_default not in all_soil_types:
        all_soil_types = [soil_type_default] + all_soil_types

    area_ha = poly.area * 111 * 111 if poly else 0  # Грубо для EPSG:4326

    with ui.row().classes('w-full'):
        with ui.column().classes('w-2/3'):
            m = ui.leaflet(center=[lat_center, lng_center], zoom=13).classes('h-96 w-full')
            if coords_latlng:
                m.generic_layer(name='polygon', args=[coords_latlng, {'color': 'red', 'weight': 2}])
        with ui.column().classes('w-1/3'):
            ui.label('Информация о поле').classes('text-h6')
            table_data = [
                {'Параметр': 'Название поля', 'Значение': field.name},
                {'Параметр': 'Площадь (га)', 'Значение': f'{area_ha:.2f}'},
                {'Параметр': 'Тип почвы', 'Значение': soil_type_default},
            ]
            ui.table(columns=[{'name': 'Параметр', 'label': 'Параметр', 'field': 'Параметр'}, {'name': 'Значение', 'label': 'Значение', 'field': 'Значение'}], rows=table_data).classes('mb-4')
    ui.button('Назад', on_click=lambda: ui.navigate.to("/fields")).classes('mt-4') 