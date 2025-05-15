from nicegui import ui, events
from db import Session, Field, Polygon, PolygonPoint
import json
from datetime import datetime
import os

def export_all_fields_to_geojson(user_id, filename="polygons.geojson"):
    session = Session()
    fields = session.query(Field).filter(Field.user_id == user_id).all()
    session.close()
    features = []
    for field in fields:
        coords = json.loads(field.coordinates)
        geojson_coords = [[lng, lat] for lat, lng in coords]
        if geojson_coords and geojson_coords[0] != geojson_coords[-1]:
            geojson_coords.append(geojson_coords[0])
        features.append({
            "type": "Feature",
            "properties": {"id": field.id, "name": field.name},
            "geometry": {
                "type": "Polygon",
                "coordinates": [geojson_coords]
            }
        })
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
        if feature["properties"]["id"] == field_id:
            coords = feature["geometry"]["coordinates"][0]
            return [[lat, lng] for lng, lat in coords]
    return None

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    polygon_coords = None
    if (action in ['edit', 'select']) and fields:
        polygon_coords = get_polygon_coords_from_geojson(int(fields))

    def handle_draw(e: events.GenericEventArguments):
        coords = e.args['layer'].get('_latlngs') or e.args['layer'].get('_latlng')
        if not coords:
            ui.notify('Не удалось получить координаты объекта', color='negative')
            return
        if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], dict):
            coords_arr = [[p['lat'], p['lng']] for p in coords]
        elif isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list):
            coords_arr = coords
        else:
            coords_arr = coords
        show_save_dialog(coords_arr)

    def handle_edit(e: events.GenericEventArguments):
        coords = e.args['layer'].get('_latlngs') or e.args['layer'].get('_latlng')
        if not coords:
            ui.notify('Не удалось получить новые координаты', color='negative')
            return
        if isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], dict):
            coords_arr = [[p['lat'], p['lng']] for p in coords]
        elif isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list):
            coords_arr = coords
        else:
            coords_arr = coords
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        if field:
            field.coordinates = json.dumps(coords_arr)
            field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            ui.notify('Полигон успешно обновлён', color='positive')
            export_all_fields_to_geojson(ui.page.user_id)
        else:
            ui.notify('Поле не найдено', color='negative')
        session.close()

    def show_save_dialog(coords_arr):
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label('Сохранить новый полигон').classes('text-h6 q-mb-md')
            name_input = ui.input(label='Название').classes('w-full q-mb-sm')
            group_input = ui.input(label='Группа').classes('w-full q-mb-sm')
            notes_input = ui.textarea(label='Заметки').classes('w-full q-mb-md')
            def save():
                if not name_input.value:
                    ui.notify('Введите название', type='warning')
                    return
                session = Session()
                try:
                    polygon = Polygon(
                        user_id=ui.page.user_id,
                        coords=json.dumps(coords_arr)
                    )
                    session.add(polygon)
                    session.flush()
                    if (isinstance(coords_arr, list) and len(coords_arr) > 0 and
                        isinstance(coords_arr[0], list) and len(coords_arr[0]) == 2 and
                        isinstance(coords_arr[0][0], (int, float))):
                        points = coords_arr
                    elif (isinstance(coords_arr, list) and len(coords_arr) > 0 and
                          isinstance(coords_arr[0], list)):
                        points = coords_arr[0]
                    else:
                        points = coords_arr
                    for lat, lng in points:
                        point_obj = PolygonPoint(
                            user_id=ui.page.user_id,
                            lat=lat,
                            lng=lng,
                            polygon_id=polygon.id
                        )
                        session.add(point_obj)
                    field = Field(
                        user_id=ui.page.user_id,
                        name=name_input.value,
                        coordinates=json.dumps(coords_arr),
                        group=group_input.value,
                        notes=notes_input.value,
                        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    session.add(field)
                    session.commit()
                    ui.notify('Полигон успешно создан', color='positive')
                    dialog.close()
                    export_all_fields_to_geojson(ui.page.user_id)
                    ui.open('/fields')
                except Exception as e:
                    session.rollback()
                    ui.notify(f'Ошибка при создании полигона: {e}', color='negative')
                finally:
                    session.close()
            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Сохранить', on_click=save).props('color=positive')
        dialog.open()

    map_view = ui.leaflet(center=(51.505, -0.09), zoom=9, draw_control=True).classes('h-96 w-full')
    map_view.on('draw:created', handle_draw)
    if action == 'edit':
        map_view.on('draw:edited', handle_edit)

    if polygon_coords:
        def on_map_ready(e):
            map_view.generic_layer(name='polygon', args=[polygon_coords, {'color': 'red', 'weight': 2}])
            if polygon_coords and len(polygon_coords) > 0:
                lat = sum(p[0] for p in polygon_coords) / len(polygon_coords)
                lng = sum(p[1] for p in polygon_coords) / len(polygon_coords)
                map_view.set_center((lat, lng))
        map_view.on('map:ready', on_map_ready)

    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')