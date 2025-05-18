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
            polygon_coords = json.loads(field.coordinates)

    if action == "edit" and polygon_coords:
        center = get_polygon_center(polygon_coords)
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
        center = get_polygon_center(polygon_coords)
        m = ui.leaflet(center=center, zoom=13, draw_control=False).classes('h-96 w-full')
        m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'blue', 'weight': 2}])

    elif action == "create":
        # Показываем только пустую карту для создания нового полигона
        m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=True).classes('h-96 w-full')

        def handle_draw(e: events.GenericEventArguments):
            coords = e.args['layer']['_latlngs']
            def save_polygon():
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
                    ui.notify('Полигон успешно создан', color='positive')
                    ui.open('/fields')
                except Exception as ex:
                    session.rollback()
                    ui.notify(f'Ошибка при создании полигона: {ex}', color='negative')
                finally:
                    session.close()
            ui.dialog(
                title='Создать новое поле?',
                content=ui.label('Вы уверены, что хотите создать новый полигон?'),
                actions=[
                    ui.button('Создать', on_click=save_polygon),
                    ui.button('Отмена', on_click=lambda: ui.notify('Создание отменено', color='warning'))
                ]
            ).open()
        m.on('draw:created', handle_draw)

    else:
        ui.label('Некорректный режим карты')

    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')