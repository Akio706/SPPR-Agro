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
        def on_move_end(e):
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
    if action == 'edit' or field_id:
        field_to_highlight = None
        if field_id:
            # Получаем поле для подсветки
            with Session() as session:
                field_to_highlight = session.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()
                if not field_to_highlight:
                    ui.notify(f'Поле с id={field_id} не найдено', color='negative')
                    # Если поле не найдено, возможно, стоит перенаправить или показать пустую карту
                    ui.navigate.to('/fields') # Перенаправляем обратно на список полей
                    return

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
                'edit': True if action == 'edit' and field_to_highlight else False,
                'remove': True if action == 'edit' and field_to_highlight else False,
            },
        }
        # Центрируем карту на выбранном поле, если оно есть
        initial_center = (55.75, 37.62)
        initial_zoom = 9
        if field_to_highlight and field_to_highlight.coordinates:
             try:
                 coords = json.loads(field_to_highlight.coordinates)
                 normalized_coords = normalize_coords(coords)
                 if normalized_coords:
                     # Приблизительное центрирование по первой координате полигона
                     initial_center = (normalized_coords[0][0], normalized_coords[0][1])
                     # Можно добавить логику для вычисления центра bounding box для лучшего центрирования
             except Exception as e:
                 print(f"Ошибка при центрировании карты: {e}")


        m = ui.leaflet(center=initial_center, zoom=initial_zoom, draw_control=draw_control, hide_drawn_items=True).classes('h-96 w-full')

        # Рисуем все остальные поля
        draw_all_user_fields(m, user_id, exclude_id=field_id)

        # Рисуем выбранное поле с подсветкой, если оно есть
        if field_to_highlight and field_to_highlight.coordinates:
             try:
                 coords = json.loads(field_to_highlight.coordinates)
                 normalized_coords = normalize_coords(coords)
                 if normalized_coords and len(normalized_coords) >= 3:
                     # Отрисовываем выбранное поле с другим стилем для подсветки
                     m.generic_layer(name=f'highlighted_polygon_{field_to_highlight.id}', args=[normalized_coords, {'color': 'red', 'weight': 4}]) # Используем красный цвет и более толстую линию для подсветки
                     # Если режим редактирования, делаем слой редактируемым
                     if action == 'edit':
                          m.run_method(f'map.editTools.editLayer(map.drawnItems.getLayer(map.leafletElements["highlighted_polygon_{field_to_highlight.id}"]))') # Активируем редактирование для подсвеченного слоя

             except Exception as e:
                 ui.notify(f'Ошибка отображения поля с id={field_to_highlight.id}: {e}', color='negative')

        # --- Тулбокс для отображения зон почв через geojson ---
        soil_geojson_layer = {'layer': None}
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
        def on_move_end(e):
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
                    field_to_highlight.name = name_input.value
                    field_to_highlight.notes = note_input.value
                    field_to_highlight.coordinates = json.dumps(edited_coords['value'])
                    field_to_highlight.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

        # Добавляем кнопки "Сохранить изменения" и "Отмена" только если в режиме редактирования
        if action == 'edit' and field_to_highlight:
             # Добавляем поля ввода для имени и заметки в режиме редактирования
             name_input = ui.input('Название поля', value=field_to_highlight.name).classes('mb-2')
             note_input = ui.input('Заметка', value=field_to_highlight.notes).classes('mb-2')
             with ui.row().classes('mt-4'):
                 ui.button('Сохранить изменения', on_click=lambda: ui.run_javascript(f'map.fireEvent("draw:edited", {{ layers: map.drawnItems }})')).props('color=positive') # Запускаем событие draw:edited
                 ui.button('Отмена редактирования', on_click=lambda: ui.navigate.to(f'/map?field_id={field_to_highlight.id}')).props('color=negative') # Отмена - возвращаемся в режим просмотра

        # Добавляем обработчик для события draw:edited
        def on_draw_edited(e):
             # Логика сохранения изменений полигона (взять из вашего существующего кода редактирования)
             print("Редактирование завершено", e.args)
             # Здесь должна быть ваша логика сохранения отредактированных координат в базу данных
             if 'layers' in e.args and field_to_highlight:
                 edited_layers = e.args['layers']
                 edited_field_layer = edited_layers.getLayer(m.leafletElements[f'highlighted_polygon_{field_to_highlight.id}'])
                 if edited_field_layer:
                      edited_coords = edited_field_layer._latlngs # Получаем новые координаты
                      normalized_edited_coords = normalize_coords(edited_coords)
                      if normalized_edited_coords:
                          field_to_highlight.coordinates = json.dumps(normalized_edited_coords)
                          field_to_highlight.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                          with Session() as session:
                               session.merge(field_to_highlight)
                               session.commit()
                          ui.notify('Изменения сохранены', color='positive')
                      else:
                           ui.notify('Не удалось получить координаты измененного полигона', color='warning')
                 else:
                      ui.notify('Не удалось найти измененный слой для сохранения', color='warning')

        m.on('draw:edited', on_draw_edited) # Подписываемся на событие только в режиме редактирования

        return # Завершаем функцию здесь, если обрабатываем просмотр/редактирование

    # --- Если ничего не выбрано, просто карта ---
    ui.label('Выберите действие: создать или редактировать поле').classes('text-h6 q-mb-md')
    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

    # Этот блок кода будет выполнен, если action не 'create' и не 'edit', и field_id отсутствует.
    # Создаем карту для общего просмотра
    m = ui.leaflet(center=(55.75, 37.62), zoom=9).classes('h-96 w-full')
    draw_all_user_fields(m, user_id) # Отображаем все поля пользователя

    # --- Тулбокс для отображения зон почв через geojson ---
    soil_geojson_layer = {'layer': None}
    def fetch_and_show_soil_geojson(bounds):
        min_lat = bounds['_southWest']['lat']
        min_lng = bounds['_southWest']['lng']
        max_lat = bounds['_northEast']['lat']
        max_lng = bounds['_northEast']['lng']
        # Убедитесь, что этот URL правильный и API эндпоинт soil_geojson работает
        url = f'http://localhost:8080/api/soil_geojson?min_lat={min_lat}&min_lng={min_lng}&max_lat={max_lat}&max_lng={max_lng}'
        try:
            geojson = requests.get(url).json()
            if soil_geojson_layer['layer']:
                m.remove_layer(soil_geojson_layer['layer'])
            # Убедитесь, что geojson данные корректны для добавления на карту
            if geojson and ('features' in geojson or 'coordinates' in geojson): # Простая проверка структуры
                 soil_geojson_layer['layer'] = m.geo_json(geojson)
            else:
                 ui.notify('Получены некорректные данные GeoJSON', color='warning')

        except Exception as ex:
            ui.notify(f'Ошибка загрузки geojson: {ex}', color='warning')

    def on_move_end(e):
        # Если soil_geojson_state['visible'] (что теперь всегда true в этом контексте), загружаем данные
        fetch_and_show_soil_geojson(e.args['bounds'])

    # Подписываемся на событие moveend для всех режимов карты
    m.on('moveend', on_move_end)

    # Кнопка "Назад" - оставлена в каждом блоке создания карты
    ui.button('Назад', on_click=lambda: ui.navigate.to('/fields')).classes('mt-4')

    ui.page('/map')(map_page)