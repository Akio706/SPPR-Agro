from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

# Подключаем Leaflet Draw CSS и JS
ui.add_head_html("""
<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css\"/>
<script src=\"https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js\"></script>
""")

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    # Карта без draw_control, но с поддержкой рисования через кастомный JS
    map_view = ui.leaflet(center=(51.505, -0.09), zoom=9).style('height: 400px; width: 100%;')

    # Инициализация инструментов рисования после полной загрузки карты
    ui.run_javascript(f"""
    document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
        var map = window.mapInstances['{map_view.id}'];
        if (!map) return;
        if (window._drawControl) {{
            map.removeControl(window._drawControl);
            window._drawControl = null;
        }}
        if (window.drawnItems) {{
            window.drawnItems.clearLayers();
        }} else {{
            window.drawnItems = new L.FeatureGroup();
            map.addLayer(window.drawnItems);
        }}
        window._drawControl = new L.Control.Draw({{
            edit: {{
                featureGroup: window.drawnItems
            }},
            draw: {{
                polygon: true,
                marker: true,
                circle: true,
                rectangle: true,
                polyline: true,
                circlemarker: true
            }}
        }});
        map.addControl(window._drawControl);
        if (window._drawCreatedHandler) {{
            map.off(L.Draw.Event.CREATED, window._drawCreatedHandler);
        }}
        window._drawCreatedHandler = function (e) {{
            var layer = e.layer;
            window.drawnItems.addLayer(layer);
            var coords = null;
            if (layer.getLatLngs) {{
                var latlngs = layer.getLatLngs();
                if (Array.isArray(latlngs) && latlngs.length > 0) {{
                    coords = [latlngs[0].map(function(pt) {{ return {{lat: pt.lat, lng: pt.lng}}; }})];
                }}
            }} else if (layer.getLatLng) {{
                var latlng = layer.getLatLng();
                coords = [[{{lat: latlng.lat, lng: latlng.lng}}]];
            }}
            if (coords) {{
                window.nicegui.send_event('polygon_drawn', {{coords: coords}});
            }} else {{
                window.nicegui.notify('Не удалось получить координаты объекта', 'negative');
            }}
        }};
        map.on(L.Draw.Event.CREATED, window._drawCreatedHandler);
    }}, {{ once: true }});
    """)

    # Показываем все существующие поля пользователя как полигоны
    session = Session()
    user_fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
    session.close()
    for field in user_fields:
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

    def on_polygon_drawn(e):
        coords = e.args['coords']
        if coords and isinstance(coords, list):
            show_save_dialog(coords)
        else:
            ui.notify('Не удалось получить координаты полигона', color='negative')

    ui.on('polygon_drawn', on_polygon_drawn)

    if action == 'edit' and fields:
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
                ui.open('/fields')
            else:
                ui.notify('Ошибка при обновлении поля', color='negative')
            session.close()
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4') 