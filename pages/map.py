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
    # Рекурсивно приводит координаты к формату [[lat, lng], ...]
    if not coords or not isinstance(coords, list):
        return []
    # Если первый элемент — список, возможно, это вложенность (например, для полигонов)
    if isinstance(coords[0], list):
        # Если это список списков, рекурсивно разворачиваем
        return [item for sub in coords for item in normalize_coords(sub)]
    # Если первый элемент — словарь
    if isinstance(coords[0], dict):
        return [[p['lat'], p['lng']] for p in coords if 'lat' in p and 'lng' in p]
    # Если первый элемент — кортеж или список с двумя числами
    if isinstance(coords[0], (tuple, list)) and len(coords[0]) == 2:
        return [[p[0], p[1]] for p in coords]
    return []

def get_polygon_center(coords):
    if not coords or not isinstance(coords, list):
        return (55.75, 37.62)
    # Если coords — список списков (lat, lng)
    if isinstance(coords[0], (list, tuple)):
        lats = [p[0] for p in coords]
        lngs = [p[1] for p in coords]
    # Если coords — список словарей {'lat': ..., 'lng': ...}
    elif isinstance(coords[0], dict):
        lats = [p['lat'] for p in coords]
        lngs = [p['lng'] for p in coords]
    else:
        return (55.75, 37.62)
    return (sum(lats) / len(lats), sum(lngs) / len(lngs))

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    polygon_coords = None
    if fields:
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        session.close()
        if field:
            polygon_coords = normalize_coords(json.loads(field.coordinates))

    if action == "edit" and polygon_coords is not None:
        center = get_polygon_center(polygon_coords) if polygon_coords else (55.75, 37.62)
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
        m = ui.leaflet(center=center, zoom=13, draw_control=draw_control).classes('h-96 w-full')
        if polygon_coords and isinstance(polygon_coords, list) and len(polygon_coords) >= 3:
            m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'red', 'weight': 2}])

        def handle_edit(e: events.GenericEventArguments):
            coords = normalize_coords(e.args['layers'][0]['_latlngs'])
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

    elif action == "select" and polygon_coords is not None:
        center = get_polygon_center(polygon_coords) if polygon_coords else (55.75, 37.62)
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
                'edit': False,
                'remove': False,
            },
        }
        m = ui.leaflet(center=center, zoom=13, draw_control=draw_control).classes('h-96 w-full')
        if polygon_coords and isinstance(polygon_coords, list) and len(polygon_coords) >= 3:
            m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'blue', 'weight': 2}])

    elif action == "create":
        m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=True).classes('h-96 w-full')

        def handle_draw(e: events.GenericEventArguments):
            coords = normalize_coords(e.args['layer']['_latlngs'])
            session = Session()
            try:
                field = Field(
                    user_id=ui.page.user_id,
                    name=f"Поле {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    coordinates=json.dumps(coords),
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                session.add(field)
                session.commit()
                def close_dialog():
                    dialog.close()
                    ui.open('/fields')
                with ui.dialog() as dialog:
                    ui.label('Полигон успешно создан!').classes('text-h6 q-mb-md')
                    ui.button('ОК', on_click=close_dialog).props('color=primary')
                dialog.open()
            except Exception as ex:
                session.rollback()
                with ui.dialog() as dialog:
                    ui.label(f'Ошибка при создании полигона: {ex}').classes('text-h6 q-mb-md')
                    ui.button('Закрыть', on_click=dialog.close).props('color=negative')
                dialog.open()
            finally:
                session.close()
        m.on('draw:created', handle_draw)

    else:
        ui.label('Некорректный режим карты')

    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')