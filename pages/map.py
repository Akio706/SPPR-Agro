from nicegui import ui, events
from db import Session, Field, Polygon, PolygonPoint
import json
from datetime import datetime

def map_page(action=None, fields=None, field_id=None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    # Получаем координаты для редактирования/показа
    polygon_coords = None
    if (action in ['edit', 'select']) and fields:
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        session.close()
        if field:
            coords = json.loads(field.coordinates)
            polygon_coords = coords[0] if isinstance(coords, list) and coords else coords

    def handle_draw(e: events.GenericEventArguments):
        coords = e.args['layer']['_latlngs']
        show_save_dialog(coords)

    def handle_edit(e: events.GenericEventArguments):
        coords = e.args['layer']['_latlngs']
        # Сохраняем новые координаты в БД
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        if field:
            field.coordinates = json.dumps([coords])
            field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            ui.notify('Полигон успешно обновлён', color='positive')
        else:
            ui.notify('Поле не найдено', color='negative')
        session.close()

    def show_save_dialog(coords):
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
                    field = Field(
                        user_id=ui.page.user_id,
                        name=name_input.value,
                        coordinates=json.dumps([coords]),
                        group=group_input.value,
                        notes=notes_input.value,
                        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    session.add(field)
                    session.commit()
                    ui.notify('Полигон успешно создан', color='positive')
                    dialog.close()
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
            'edit': action == 'edit',
            'remove': False,
        },
    }

    m = ui.leaflet(center=(55.75, 37.62), draw_control=draw_control)
    m.on('draw:created', handle_draw)
    if action == 'edit':
        m.on('draw:edited', handle_edit)

    # После инициализации карты — добавляем полигон
    if polygon_coords:
        @m.on('map:ready')
        def _(e):
            m.generic_layer(name='polygon', args=[polygon_coords, {'color': 'red', 'weight': 2}])

    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')