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

def normalize_coords(coords):
    """Универсально приводит к формату [[lat, lng], ...]"""
    if not coords or not isinstance(coords, list):
        return []
    if isinstance(coords[0], list):
        return [item for sub in coords for item in normalize_coords(sub)]
    if isinstance(coords[0], dict):
        return [[float(p['lat']), float(p['lng'])] for p in coords if 'lat' in p and 'lng' in p]
    if isinstance(coords[0], (tuple, list)) and len(coords[0]) == 2:
        return [[float(p[0]), float(p[1])] for p in coords]
    return []

def get_polygon_center(coords):
    """Вычисляет центр полигона"""
    coords = normalize_coords(coords)
    if not coords:
        return (55.75, 37.62)
    lats = [p[0] for p in coords]
    lngs = [p[1] for p in coords]
    return (sum(lats) / len(lats), sum(lngs) / len(lngs))

def show_leaflet_map(center, draw_control, polygon_coords=None, color='red', on_edit=None):
    """Универсальный рендер карты с опциональным полигоном"""
    m = ui.leaflet(center=center, zoom=13, draw_control=draw_control).classes('h-96 w-full')
    if polygon_coords and len(polygon_coords) >= 3:
        m.generic_layer(name='polygon', args=[polygon_coords, {'color': color, 'weight': 2}])
    if on_edit:
        m.on('draw:edited', on_edit)
    return m

def map_page(action: str = None, fields: str = None, field_id: str = None):
    ui.add_head_html('<link rel="stylesheet" href="/static/leaflet.css">')
    ui.add_head_html('<script src="/static/leaflet.js"></script>')
    ui.add_head_html('<script src="/static/leaflet.draw.js"></script>')
    # if not getattr(ui.page, 'user_id', None):
    #     return ui.open('/')

    polygon_coords = None
    field = None
    if fields:
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        if field:
            raw_coords = json.loads(field.coordinates)
            polygon_coords = normalize_coords(raw_coords)
            # Автоматическая миграция: если исходные координаты были в виде списка словарей, сохраняем в базе как список списков
            if polygon_coords and isinstance(raw_coords, list) and isinstance(raw_coords[0], dict):
                field.coordinates = json.dumps(polygon_coords)
                session.commit()
        session.close()

    if action in ("edit", "select") and field:
        center = get_polygon_center(polygon_coords) if polygon_coords and len(polygon_coords) >= 3 else (55.75, 37.62)
        draw_control = {
            'draw': {
                'polygon': action == "edit",
                'marker': False,
                'circle': False,
                'rectangle': False,
                'polyline': False,
                'circlemarker': False,
            },
            'edit': {
                'edit': action == "edit",
                'remove': False,
            },
        }
        m = ui.leaflet(center=center, zoom=13, draw_control=draw_control, hide_drawn_items=True).classes('h-96 w-full')
        m.tile_layer(url_template="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        if polygon_coords and len(polygon_coords) >= 3:
            m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'red' if action=="edit" else 'blue', 'weight': 2}])
        if action == "edit":
            def handle_draw(e: events.GenericEventArguments):
                coords = normalize_coords(e.args['layer']['_latlngs'])
                session = Session()
                f = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
                if f:
                    f.coordinates = json.dumps(coords)
                    f.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()
                    ui.notify('Полигон успешно сохранён', color='positive')
                else:
                    ui.notify('Поле не найдено', color='negative')
                session.close()
            def handle_edit(e: events.GenericEventArguments):
                coords = normalize_coords(e.args['layers'][0]['_latlngs'])
                session = Session()
                f = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
                if f:
                    f.coordinates = json.dumps(coords)
                    f.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()
                    ui.notify('Полигон успешно обновлён', color='positive')
                else:
                    ui.notify('Поле не найдено', color='negative')
                session.close()
            m.on('draw:created', handle_draw)
            m.on('draw:edited', handle_edit)
        # Форма редактирования параметров поля
        with ui.form().classes('q-gutter-md q-mt-md') as form:
            name = ui.input('Название', value=field.name).classes('w-full')
            area = ui.input('Площадь', value=str(field.area) if field.area else '').props('type=number').classes('w-full')
            soil_type = ui.input('Тип почвы', value=field.soil_type or '').classes('w-full')
            notes = ui.input('Заметки', value=field.notes or '').classes('w-full')
            def save_params():
                session = Session()
                f = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
                if f:
                    f.name = name.value
                    f.area = float(area.value) if area.value else None
                    f.soil_type = soil_type.value
                    f.notes = notes.value
                    f.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()
                    ui.notify('Параметры поля сохранены', color='positive')
                session.close()
            ui.button('Сохранить параметры', on_click=save_params).props('color=primary')
    elif action == "create":
        draw_control = {
            'draw': {
                'polygon': True,
                'marker': False,
                'circle': False,
                'rectangle': False,
                'polyline': False,
                'circlemarker': False,
            },
            'edit': {
                'edit': False,
                'remove': False,
            },
        }
        m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=draw_control, hide_drawn_items=True).classes('h-96 w-full')
        m.tile_layer(url_template="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        def handle_draw(e: events.GenericEventArguments):
            options = {'color': 'red', 'weight': 1}
            m.generic_layer(name='polygon', args=[e.args['layer']['_latlngs'], options])
        m.on('draw:created', handle_draw)
    else:
        ui.label('Поле не найдено или не выбрано').classes('text-h6 q-mb-md')
    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')

def handle_draw(e: events.GenericEventArguments):
    options = {'color': 'red', 'weight': 1}
    m.generic_layer(name='polygon', args=[e.args['layer']['_latlngs'], options])

draw_control = {
    'draw': {
        'polygon': True,
        'marker': False,
        'circle': False,
        'rectangle': False,
        'polyline': False,
        'circlemarker': False,
    },
    'edit': {
        'edit': False,
        'remove': False,
    },
}
m = ui.leaflet(center=(51.5, 0), zoom=13, draw_control=draw_control, hide_drawn_items=True)
m.tile_layer(url_template="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
m.on('draw:created', handle_draw)

ui.run()