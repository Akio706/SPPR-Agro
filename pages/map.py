from nicegui import ui, events
from db import Session, Field, Polygon, PolygonPoint
import json
from datetime import datetime

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    def handle_draw(e: events.GenericEventArguments):
        coords = e.args['layer'].get('_latlngs') or e.args['layer'].get('_latlng')
        if not coords:
            ui.notify('Не удалось получить координаты объекта', color='negative')
            return
        show_save_dialog(coords)

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
                    # 1. Сохраняем сам полигон (Polygon)
                    polygon = Polygon(
                        user_id=ui.page.user_id,
                        coords=json.dumps(coords)
                    )
                    session.add(polygon)
                    session.flush()  # Получаем polygon.id

                    # 2. Проверяем структуру coords
                    if not (isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], list)):
                        raise ValueError(f"Некорректная структура координат: {coords}")

                    # 3. Сохраняем точки полигона (PolygonPoint)
                    for point in coords[0]:
                        if not all(k in point for k in ('lat', 'lng')):
                            raise ValueError(f"Некорректная точка: {point}")
                        point_obj = PolygonPoint(
                            user_id=ui.page.user_id,
                            lat=point['lat'],
                            lng=point['lng'],
                            polygon_id=polygon.id
                        )
                        session.add(point_obj)

                    # 4. Создаём запись в таблице Field
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

    map_view = ui.leaflet(center=(51.505, -0.09), zoom=9, draw_control=True).classes('h-96 w-full')
    map_view.on('draw:created', handle_draw)

    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')