from nicegui import ui, events
from db import Session, Field, Polygon, PolygonPoint
import json
from datetime import datetime
import os
from utils import geojson_from_coords, coords_from_geojson

def export_all_fields_to_geojson(user_id, filename="polygons.geojson"):
    session = Session()
    fields = session.query(Field).filter(Field.user_id == user_id).all()
    session.close()
    features = []
    for field in fields:
        coords = json.loads(field.coordinates)
        geojson = geojson_from_coords(coords, field.name)
        geojson["properties"]["id"] = field.id
        features.append(geojson)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

def get_polygon_coords_from_geojson(field_id, filename="polygons.geojson"):
    if not os.path.exists(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    for feature in geojson["features"]:
        if feature["properties"].get("id") == field_id:
            return coords_from_geojson(feature)
    return None

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    polygon_coords = None
    if fields:
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        session.close()
        if field:
            polygon_coords = json.loads(field.coordinates)

    if action == "edit" and polygon_coords:
        draw_control = {
            'draw': {
                'polygon': False,
                'marker': False,
                'circle': False,
                'rectangle': False,
                'polyline': False,
                'circlemarker': False,
            },
            'edit': {
                'edit': True,
                'remove': False,
            },
        }
        m = ui.leaflet(center=(polygon_coords[0][0], polygon_coords[0][1]), zoom=13, draw_control=draw_control).classes('h-96 w-full')
        m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'red', 'weight': 2}])

        def handle_edit(e: events.GenericEventArguments):
            coords = e.args['layers'][0]['_latlngs']
            session = Session()
            field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
            if field:
                field.coordinates = json.dumps(coords)
                field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.commit()
                ui.notify('Полигон успешно обновлён', color='positive')
            else:
                ui.notify('Поле не найдено', color='negative')
            session.close()
        m.on('draw:edited', handle_edit)

    elif action == "select" and polygon_coords:
        m = ui.leaflet(center=(polygon_coords[0][0], polygon_coords[0][1]), zoom=13, draw_control=False).classes('h-96 w-full')
        m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'blue', 'weight': 2}])

    else:
        session = Session()
        user_fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
        session.close()
        polygons = [json.loads(field.coordinates) for field in user_fields]
        m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=True).classes('h-96 w-full')
        for coords in polygons:
            m.generic_layer(name='polygon', args=[coords, {'color': 'red', 'weight': 1}])

    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')