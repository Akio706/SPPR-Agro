from nicegui import ui
from db import Session, Field
import json
from datetime import datetime

# Подключаем только Leaflet Draw (CSS и JS)
ui.add_head_html("""
<link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
""")


def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        ui.run_javascript("window.location.href = '/';")
        return

    map_view = ui.leaflet(center=(55.75, 37.62), zoom=6).style('height: 500px; width: 100%;')

    # --- СОЗДАНИЕ ПОЛИГОНА ---
    if action == 'create':
        ui.run_javascript(f"""
        document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
            const map = window.mapInstances['{map_view.id}'];
            if (!map) return;
            // Initialize the draw control
            if (!window.drawnItems) {{
                window.drawnItems = new L.FeatureGroup();
                map.addLayer(window.drawnItems);
            }}
            const drawControl = new L.Control.Draw({{
                edit: {{ featureGroup: window.drawnItems }},
                draw: {{
                    polygon: true,
                    marker: false,
                    circle: false,
                    rectangle: false,
                    polyline: false,
                    circlemarker: false
                }}
            }});
            map.addControl(drawControl);

            map.on(L.Draw.Event.CREATED, function (e) {{
                const layer = e.layer;
                window.drawnItems.addLayer(layer);
                const latlngs = layer.getLatLngs()[0].map(pt => {{ return {{ lat: pt.lat, lng: pt.lng }}; }});
                window.nicegui.send_event('polygon_drawn', {{ coords: [latlngs] }});
            }});
        }});
        """)

    # --- РЕДАКТИРОВАНИЕ ПОЛИГОНА ---
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
        lat = sum(p['lat'] for p in latlngs) / len(latlngs)
        lng = sum(p['lng'] for p in latlngs) / len(latlngs)
        map_view.set_center((lat, lng))
        js_coords = json.dumps([[p['lat'], p['lng']] for p in latlngs])

        ui.run_javascript(f"""
        document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
            const map = window.mapInstances['{map_view.id}'];
            if (!map) return;

            if (!window.drawnItems) {{
                window.drawnItems = new L.FeatureGroup();
                map.addLayer(window.drawnItems);
            }}
            const poly = L.polygon({js_coords}, {{ color: 'orange', weight: 3 }}).addTo(window.drawnItems);
            map.fitBounds(poly.getBounds());
            window._editPoly = poly;
        }});

        function saveEditedPolygon() {{
            const poly = window._editPoly;
            if (!poly) {{
                window.nicegui.notify('Полигон не найден для сохранения', 'negative');
                return;
            }}
            const latlngs = poly.getLatLngs()[0].map(pt => {{ return {{ lat: pt.lat, lng: pt.lng }}; }});
            window.nicegui.send_event('save_edited_poly', {{ latlngs: latlngs }});
        }}
        """)

        def on_save_edited_poly(e):
            new_coords = [e.args['latlngs']]
            session = Session()
            try:
                field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
                if field:
                    field.coordinates = json.dumps(new_coords)
                    field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    session.commit()
                    ui.notify('Поле успешно обновлено', color='positive')
                    ui.run_javascript("window.location.href = '/fields';")
                else:
                    ui.notify('Ошибка при обновлении поля', color='negative')
            except Exception as ex:
                session.rollback()
                ui.notify(f'Ошибка при сохранении изменений: {ex}', color='negative')
            finally:
                session.close()

        ui.on('save_edited_poly', on_save_edited_poly)
        ui.button('Сохранить изменения', on_click=lambda: ui.run_javascript("saveEditedPolygon();")).classes('mt-4')

    # --- ПРОСМОТР ВСЕХ ПОЛЕЙ ---
    elif action == 'select' and fields:
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
        lat = sum(p['lat'] for p in latlngs) / len(latlngs)
        lng = sum(p['lng'] for p in latlngs) / len(latlngs)
        map_view.set_center((lat, lng))
        js_coords = json.dumps([[p['lat'], p['lng']] for p in latlngs])

        ui.run_javascript(f"""
        document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
            const map = window.mapInstances['{map_view.id}'];
            if (map) {{
                L.polygon({js_coords}, {{ color: 'green', weight: 3 }}).addTo(map);
            }}
        }});
        """)

    # --- ДИАЛОГ СОХРАНЕНИЯ ПОЛЯ ---
    def show_save_dialog(coords):
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label('Сохранить новое поле').classes('text-h6 q-mb-md')
            name_input = ui.input(label='Название').classes('w-full q-mb-sm')
            group_input = ui.input(label='Группа').classes('w-full q-mb-sm')
            notes_input = ui.textarea(label='Заметки').classes('w-full q-mb-md')

            def save():
                if not name_input.value:
                    ui.notify('Введите название', color='warning')
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

    def on_polygon_drawn(e):
        coords = e.args['coords']
        if coords and isinstance(coords, list):
            show_save_dialog(coords)
        else:
            ui.notify('Не удалось получить координаты полигона', color='negative')

    ui.on('polygon_drawn', on_polygon_drawn)

    ui.button('Назад к полям', on_click=lambda: ui.run_javascript("window.location.href = '/fields';")).classes('mt-4')