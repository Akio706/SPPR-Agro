from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    map_view = ui.leaflet(center=(51.505, -0.09), zoom=9, draw_control={
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
    }).classes('h-96 w-full')

    session = Session()
    user_fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
    session.close()
    for field in user_fields:
        try:
            coords = json.loads(field.coordinates)
            latlngs = coords[0]
            js_coords = json.dumps([[p['lat'], p['lng']] for p in latlngs])
            ui.run_javascript(f'''
                window.mapInstances = window.mapInstances || {{}};
                document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
                    const map = window.mapInstances['{map_view.id}'];
                    if (map) {{
                        L.polygon({js_coords}, {{color: 'blue', weight: 2}}).addTo(map);
                    }}
                }}, {{ once: true }});
            ''')
        except Exception as e:
            print(f"Ошибка при отрисовке полигона: {e}")

    with ui.card().classes('w-full mt-4'):
        ui.label('Ваши поля').classes('text-h5 q-mb-md')
        table_rows = []
        for field in user_fields:
            table_rows.append({
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
            })
        def edit_field(field_id):
            ui.open(f'/map?action=edit&fields={field_id}')
        columns = [
            {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
            {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
            {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'},
            {'name': 'edit', 'label': '', 'field': 'edit', 'align': 'left'},
        ]
        def row_slot(row):
            with ui.row():
                ui.label(str(row['id'])).classes('q-mr-md')
                ui.label(row['name']).classes('q-mr-md')
                ui.label(row['created_at']).classes('q-mr-md')
                ui.button('Редактировать', on_click=lambda r=row: edit_field(r['id'])).props('color=primary')
        ui.table(
            columns=columns,
            rows=table_rows,
            row_key='id',
            row_slot=row_slot
        ).classes('w-full')

    if action == 'create':
        def handle_field_creation(e: events.GenericEventArguments):
            coords = None
            if '_latlngs' in e.args['layer']:
                coords = e.args['layer']['_latlngs']
            elif '_latlng' in e.args['layer']:
                coords = e.args['layer']['_latlng']
            else:
                ui.notify('Не удалось получить координаты объекта', color='negative')
                return
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
                            coordinates=json.dumps(coords),
                            group=group_input.value,
                            notes=notes_input.value,
                            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        )
                        session.add(field)
                        session.commit()
                        ui.notify('Поле успешно создано', color='positive')
                        dialog.close()
                        ui.open('/map')
                    except Exception as e:
                        session.rollback()
                        ui.notify(f'Ошибка при создании поля: {e}', color='negative')
                    finally:
                        session.close()
                with ui.row().classes('w-full justify-end'):
                    ui.button('Отмена', on_click=dialog.close).props('flat')
                    ui.button('Сохранить', on_click=save).props('color=positive')
            dialog.open()
        map_view.on('draw:created', handle_field_creation)
    elif action == 'edit' and fields:
        try:
            field_id = int(fields)
        except (TypeError, ValueError):
            ui.notify('Некорректный ID поля', color='negative')
            return
        session = Session()
        field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
        session.close()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            return
        coords = json.loads(field.coordinates)
        latlngs = coords[0]
        js_coords = json.dumps([[p['lat'], p['lng']] for p in latlngs])
        ui.run_javascript(f'''
            window.mapInstances = window.mapInstances || {{}};
            document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
                const map = window.mapInstances['{map_view.id}'];
                if (map) {{
                    let poly = L.polygon({js_coords}, {{color: 'orange', weight: 3}}).addTo(map);
                    map.fitBounds(poly.getBounds());
                    if (map.editTools) {{
                        poly.enableEdit();
                    }}
                    window._editPoly = poly;
                }}
            }}, {{ once: true }});
        ''')
        def save_edited():
            ui.run_javascript(f'''
                (function() {{
                    const poly = window._editPoly;
                    if (!poly) {{
                        window.nicegui.notify('Полигон не найден для сохранения', 'negative');
                        return;
                    }}
                    const latlngs = poly.getLatLngs()[0].map(pt => {{ return {{lat: pt.lat, lng: pt.lng}} }});
                    window.nicegui.send_event('save_edited_poly', {{latlngs: latlngs}});
                }})();
            ''')
        @ui.event('save_edited_poly')
        def on_save_edited_poly(e):
            new_coords = [e.args['latlngs']]
            session = Session()
            field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
            if field:
                field.coordinates = json.dumps(new_coords)
                field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.commit()
                ui.notify('Поле успешно обновлено', color='positive')
                ui.open('/map')
            else:
                ui.notify('Ошибка при обновлении поля', color='negative')
            session.close()
        ui.button('Сохранить изменения', on_click=save_edited).classes('mt-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4') 