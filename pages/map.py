from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

def handle_draw(e: events.GenericEventArguments):
    coords = e.args['layer']['_latlngs']
    show_save_dialog(coords)

def show_save_dialog(coords):
    dialog = ui.dialog()
    with dialog, ui.card():
        ui.label('Сохранить новое поле').classes('text-h6 q-mb-md')
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
                ui.notify('Поле успешно создано', color='positive')
                dialog.close()
                ui.open('/fields')
            except Exception as e:
                session.rollback()
                ui.notify(f'Ошибка при создании поля: {e}', color='negative')
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
        'edit': False,
        'remove': False,
    },
}

m = ui.leaflet(center=(55.75, 37.62), draw_control=draw_control)
m.on('draw:created', handle_draw)

ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')
