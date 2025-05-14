from nicegui import events, ui
from db import Session, Field
import json
from datetime import datetime

# Handle the drawing of a polygon and save it to the database
def handle_draw(e: events.GenericEventArguments):
    options = {'color': 'red', 'weight': 1}
    m.generic_layer(name='polygon', args=[e.args['layer']['_latlngs'], options])

    # Extract coordinates from the drawn layer
    coords = e.args['layer']['_latlngs']

    # Show a dialog to save the drawn polygon
    dialog = ui.dialog()
    with dialog, ui.card():
        ui.label('Сохранить новое поле').classes('text-h6 q-mb-md')
        name_input = ui.input(label='Название').classes('w-full q-mb-sm')
        group_input = ui.input(label='Группа').classes('w-full q-mb-sm')
        notes_input = ui.input(label='Заметки').classes('w-full q-mb-md')

        def save():
            if not name_input.value:
                ui.notify('Введите название', type='warning')
                return

            session = Session()
            try:
                field = Field(
                    user_id=1,  # Replace with dynamic user ID if applicable
                    name=name_input.value,
                    coordinates=json.dumps(coords),
                    group=group_input.value,
                    notes=notes_input.value,
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                session.add(field)
                session.commit()
                ui.notify('Поле успешно создано', color='positive')
                dialog.close()
            except Exception as ex:
                ui.notify(f'Произошла ошибка: {str(ex)}', type='negative')
                session.rollback()
            finally:
                session.close()

        ui.button('Сохранить', on_click=save).classes('q-mt-md')

    dialog.open()

# Map configuration
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

# Create the map
m = ui.leaflet(center=(51.5, 0), draw_control=draw_control)
m.on('draw:created', handle_draw)

ui.run()