from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

# Add Leaflet.Draw CSS and JavaScript to the page
ui.add_head_html("""
<link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
""")


def handle_draw(e: events.GenericEventArguments):
    """
    Handles the drawing of polygons on the map.
    """
    options = {'color': 'red', 'weight': 1}  # Styling options for the drawn polygon
    m.generic_layer(name='polygon', args=[e.args['layer']['_latlngs'], options])


def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        ui.run_javascript("window.location.href = '/';")
        return

    # Draw control configuration
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

    # Create the map with the custom draw control
    m = ui.leaflet(center=(51.5, 0), draw_control=draw_control, hide_drawn_items=True)
    m.on('draw:created', handle_draw)  # Bind the drawing event to the handler

    # Save Dialog
    def show_save_dialog(coords):
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
                        user_id=ui.page.user_id,
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
                    ui.run_javascript("window.location.href = '/fields';")
                except Exception as ex:
                    session.rollback()
                    ui.notify(f'Ошибка при создании поля: {ex}', color='negative')
                finally:
                    session.close()

            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Сохранить', on_click=save).props('color=positive')

        dialog.open()

    # Handle the 'polygon_drawn' event
    def on_polygon_drawn(e):
        coords = e.args['coords']
        if coords and isinstance(coords, list):
            show_save_dialog(coords)
        else:
            ui.notify('Не удалось получить координаты полигона', color='negative')

    ui.on('polygon_drawn', on_polygon_drawn)

    # Button to go back to the fields page
    ui.button('Назад к полям', on_click=lambda: ui.run_javascript("window.location.href = '/fields';")).classes('mt-4')


ui.run()