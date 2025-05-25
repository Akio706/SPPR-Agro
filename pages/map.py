from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

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
        def handle_draw(e: events.GenericEventArguments):
            coords = e.args['layer']['_latlngs']
            drawn_coords['value'] = coords
            m.generic_layer(name='polygon', args=[coords, options])
            # Открываем диалог для ввода имени и заметки
            with ui.dialog() as dialog, ui.card():
                name_input = ui.input('Название поля').classes('mb-2')
                note_input = ui.input('Заметка').classes('mb-2')
                def save():
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

ui.page('/map')(map_page)