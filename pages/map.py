from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime
import psycopg2
from shapely.geometry import Polygon, shape, mapping
import geopandas as gpd
import hashlib
import os
import requests

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

def get_all_fields(user_id):
    with Session() as session:
        fields = session.query(Field).filter(Field.user_id == user_id).all()
        return fields

def handle_draw(e: events.GenericEventArguments):
    user_id = getattr(ui.page, 'user_id', None)
    if not user_id:
        ui.notify('Необходима авторизация', color='negative')
        return
    coords = e.args['layer']['_latlngs']
    coords_json = json.dumps(coords)
    with Session() as session:
        field = Field(
            user_id=user_id,
            name=f'Поле {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            coordinates=coords_json,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(field)
        session.commit()
    ui.notify('Полигон сохранён в базе', color='positive')
    ui.navigate.to('/map')

def show_all_polygons(m, user_id):
    fields = get_all_fields(user_id)
    for field in fields:
        try:
            coords = json.loads(field.coordinates)
            coords = normalize_coords(coords)
            if coords and len(coords) >= 3:
                m.generic_layer(name=f'polygon_{field.id}', args=[coords, {'color': 'blue', 'weight': 2}])
        except Exception:
            continue

def get_zones_regions_polygons():
    # Подключение к базе Postgres/PostGIS напрямую через psycopg2
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'frost_db'),
        port=os.getenv('POSTGRES_PORT', '5432'),
    )
    cur = conn.cursor()
    cur.execute("SELECT gid, ST_AsGeoJSON(geom), soil_legend_Descript FROM soil_regions_full;")
    # Генерируем цвета для каждого типа почвы
    color_map = {}
    def get_color(soil_type):
        if soil_type not in color_map:
            # Генерируем цвет на основе хеша типа почвы
            h = hashlib.md5(soil_type.encode()).hexdigest()
            color = f'#{h[:6]}'
            color_map[soil_type] = color
        return color_map[soil_type]
    result = []
    for row in cur.fetchall():
        gid, geojson, soil_type = row
        if geojson:
            gj = json.loads(geojson)
            coords_latlng = [[c[1], c[0]] for c in gj['coordinates'][0]]
            color = get_color(soil_type or "unknown")
            result.append({'gid': gid, 'coords': coords_latlng, 'color': color, 'soil_type': soil_type})
    print(f"Добавлено полигонов: {len(result)}")
    cur.close()
    conn.close()
    return result

def get_zones_regions_polygons_bbox(bbox=None):
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'postgres'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres'),
        host=os.getenv('POSTGRES_HOST', 'frost_db'),
        port=os.getenv('POSTGRES_PORT', '5432'),
    )
    cur = conn.cursor()
    # Временно убираем фильтрацию по bbox для отладки
    cur.execute("SELECT gid, ST_AsGeoJSON(geom), soil_legend_Descript FROM soil_regions_full;")
    color_map = {}
    def get_color(soil_type):
        if soil_type not in color_map:
            h = hashlib.md5((soil_type or 'unknown').encode()).hexdigest()
            color = f'#{h[:6]}'
            color_map[soil_type] = color
        return color_map[soil_type]
    result = []
    for row in cur.fetchall():
        gid, geojson, soil_type = row
        if geojson:
            gj = json.loads(geojson)
            coords_latlng = [[c[1], c[0]] for c in gj['coordinates'][0]]
            color = get_color(soil_type or "unknown")
            result.append({'gid': gid, 'coords': coords_latlng, 'color': color, 'soil_type': soil_type})
    print(f"Добавлено полигонов: {len(result)}")
    cur.close()
    conn.close()
    return result

def map_page(action: str = None, fields: str = None, field_id: str = None):
    user_id = getattr(ui.page, 'user_id', None)
    if not user_id:
        ui.label('Необходима авторизация').classes('text-h6 q-mb-md')
        return
    params = ui.page.query if hasattr(ui.page, 'query') else {}
    action = action or (params.get('action') if params else None)
    fields = fields or (params.get('fields') if params else None)
    field_id = field_id or (params.get('field_id') if params else None)

    def draw_all_user_fields(m, user_id, exclude_id=None):
        fields = get_all_fields(user_id)
        for field in fields:
            if exclude_id and str(field.id) == str(exclude_id):
                continue
            try:
                coords = json.loads(field.coordinates)
                coords = normalize_coords(coords)
                if coords and len(coords) >= 3:
                    m.generic_layer(name=f'polygon_{field.id}', args=[coords, {'color': 'blue', 'weight': 2}])
            except Exception:
                continue

    # --- Создание нового поля ---
    if action == 'create':
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
        options = {'color': 'red', 'weight': 1}
        drawn_coords = {'value': None}

        # --- Тулбокс для отображения зон почв через geojson ---
        soil_geojson_layer = {'layer': None}
        soil_geojson_state = {'visible': False}
        def fetch_and_show_soil_geojson(bounds):
            min_lat = bounds['_southWest']['lat']
            min_lng = bounds['_southWest']['lng']
            max_lat = bounds['_northEast']['lat']
            max_lng = bounds['_northEast']['lng']
            url = f'http://localhost:8080/api/soil_geojson?min_lat={min_lat}&min_lng={min_lng}&max_lat={max_lat}&max_lng={max_lng}'
            try:
                geojson = requests.get(url).json()
                if soil_geojson_layer['layer']:
                    m.remove_layer(soil_geojson_layer['layer'])
                soil_geojson_layer['layer'] = m.geo_json(geojson)
            except Exception as ex:
                ui.notify(f'Ошибка загрузки geojson: {ex}', color='warning')
        def toggle_soil_geojson(e):
            if e.value:
                soil_geojson_state['visible'] = True
                # Не вызываем fetch_and_show_soil_geojson здесь! Ждём moveend
            else:
                soil_geojson_state['visible'] = False
                if soil_geojson_layer['layer']:
                    m.remove_layer(soil_geojson_layer['layer'])
                    soil_geojson_layer['layer'] = None
        ui.checkbox('Показать карту типов почв (soil_regions_full)', value=False, on_change=toggle_soil_geojson).classes('mb-2')
        def on_move_end(e):
            if soil_geojson_state['visible']:
                fetch_and_show_soil_geojson(e.args['bounds'])
        m.on('moveend', on_move_end)

        def handle_draw(e: events.GenericEventArguments):
            coords = normalize_coords(e.args['layer']['_latlngs'])
            options = {'color': 'red', 'weight': 1}
            m.generic_layer(name='polygon', args=[coords, options])
            drawn_coords['value'] = coords
            # Открываем диалог для ввода имени и заметки
            with ui.dialog() as dialog, ui.card():
                name_input = ui.input('Название поля').classes('mb-2')
                note_input = ui.input('Заметка').classes('mb-2')
                def save():
                    # Гарантируем, что coords — список пар [lat, lng]
                    if coords and isinstance(coords[0], list) and isinstance(coords[0][0], (float, int)):
                        coords_for_poly = coords
                    elif coords and isinstance(coords[0], (float, int)):
                        coords_for_poly = [coords[i:i+2] for i in range(0, len(coords), 2)]
                    else:
                        ui.notify('Ошибка структуры координат', color='negative')
                        return
                    poly = Polygon([(lng, lat) for lat, lng in coords_for_poly])
                    area_ha = poly.area * 111 * 111  # Приблизительно, для EPSG:4326 (грубо)
                    if area_ha > 1000:
                        ui.notify('Площадь поля превышает 1000 га!', color='negative')
                        return
                    # Проверка на вхождение в soil-zones regions
                    gdf = gpd.read_file('soil_regions_full.gpkg')
                    intersects = gdf[gdf.geometry.intersects(poly)]
                    if intersects.empty:
                        ui.notify('Полигон вне границ soil-zones regions!', color='negative')
                        return
                    if not name_input.value:
                        ui.notify('Введите название поля', color='warning')
                        return
                    with Session() as session:
                        field = Field(
                            user_id=user_id,
                            name=name_input.value,
                            coordinates=json.dumps(drawn_coords['value']),
                            notes=note_input.value,
                            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        session.add(field)
                        session.commit()
                    ui.notify('Поле сохранено', color='positive')
                    dialog.close()
                    ui.navigate.to('/fields')
                ui.button('Сохранить', on_click=save).props('color=positive')
                ui.button('Отмена', on_click=dialog.close).props('color=negative')
            dialog.open()
        m.on('draw:created', handle_draw)
        ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')
        return

    # --- Редактирование/просмотр поля по ID ---
    if (action == 'edit' and (fields or field_id)) or (action == 'select' and (fields or field_id)):
        field_id = fields or field_id
        with Session() as session:
            field = session.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
            if not field:
                ui.notify('Поле не найдено', color='negative')
                ui.button('Назад', on_click=lambda: ui.navigate.to('/fields'))
                return
            name_input = ui.input('Название поля', value=field.name).classes('mb-2')
            note_input = ui.input('Заметка', value=field.notes if hasattr(field, 'notes') else '').classes('mb-2')
            coords = json.loads(field.coordinates)
            coords = normalize_coords(coords)
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
                    'edit': True if action == 'edit' else False,
                    'remove': False,
                },
            }
            m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=draw_control, hide_drawn_items=True).classes('h-96 w-full')
            options = {'color': 'red', 'weight': 1, 'editable': True}
            if coords and len(coords) >= 3:
                m.generic_layer(name='polygon', args=[coords, options])
            # --- Оптимизированное отображение geojson почв ---
            soil_geojson_layer = {'layer': None}
            soil_geojson_state = {'visible': False}
            def fetch_and_show_soil_geojson(bounds):
                min_lat = bounds['_southWest']['lat']
                min_lng = bounds['_southWest']['lng']
                max_lat = bounds['_northEast']['lat']
                max_lng = bounds['_northEast']['lng']
                url = f'http://localhost:8080/api/soil_geojson?min_lat={min_lat}&min_lng={min_lng}&max_lat={max_lat}&max_lng={max_lng}'
                try:
                    geojson = requests.get(url).json()
                    if soil_geojson_layer['layer']:
                        m.remove_layer(soil_geojson_layer['layer'])
                    soil_geojson_layer['layer'] = m.geo_json(geojson)
                except Exception as ex:
                    ui.notify(f'Ошибка загрузки geojson: {ex}', color='warning')
            def toggle_soil_geojson(e):
                if e.value:
                    soil_geojson_state['visible'] = True
                else:
                    soil_geojson_state['visible'] = False
                    if soil_geojson_layer['layer']:
                        m.remove_layer(soil_geojson_layer['layer'])
                        soil_geojson_layer['layer'] = None
            ui.checkbox('Показать карту типов почв (GeoJSON)', value=False, on_change=toggle_soil_geojson).classes('mb-2')
            def on_move_end(e):
                if soil_geojson_state['visible']:
                    fetch_and_show_soil_geojson(e.args['bounds'])
            m.on('moveend', on_move_end)
            edited_coords = {'value': coords}
            def on_draw_edited(e):
                layers = e.args.get('layers', [])
                if layers:
                    # В NiceGUI обычно e.args['layers'] — список объектов с ключом 'layer', где 'layer' содержит '_latlngs'
                    for lyr in layers:
                        if 'layer' in lyr and '_latlngs' in lyr['layer']:
                            edited_coords['value'] = lyr['layer']['_latlngs']
                            break
            if action == 'edit':
                m.on('draw:edited', on_draw_edited)
                def save_changes():
                    if not name_input.value:
                        ui.notify('Введите название поля', color='warning')
                        return
                    def do_save():
                        field.name = name_input.value
                        field.notes = note_input.value
                        field.coordinates = json.dumps(edited_coords['value'])
                        field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        session.commit()
                        ui.notify('Поле обновлено', color='positive')
                        ui.navigate.to('/fields')
                    with ui.dialog() as dialog, ui.card():
                        ui.label('Сохранить изменения?')
                        ui.button('Да', on_click=lambda: (do_save(), dialog.close())).props('color=positive')
                        ui.button('Нет', on_click=dialog.close).props('color=negative')
                    dialog.open()
                ui.button('Сохранить', on_click=save_changes).props('color=positive').classes('mt-4')
            ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')
        return

    # --- Если ничего не выбрано, просто карта ---
    ui.label('Выберите действие: создать или редактировать поле').classes('text-h6 q-mb-md')
    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

    def draw_zones_regions_layer(m):
        for poly in get_zones_regions_polygons():
            m.generic_layer(name=f'zones_{poly["gid"]}', args=[poly['coords'], {'color': poly['color'], 'weight': 1, 'opacity': 0.5}])

    # В каждом режиме после создания карты m:
    # draw_zones_regions_layer(m)

    ui.page('/map')(map_page)