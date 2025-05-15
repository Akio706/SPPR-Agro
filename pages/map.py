from nicegui import ui
from db import Session, Field
import json
from datetime import datetime

def map_page(action=None, fields=None, field_id=None):
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')

    ui.add_head_html("""
    <link rel=\"stylesheet\" href=\"/static/leaflet.css\"/>
    <link rel=\"stylesheet\" href=\"/static/leaflet.draw.css\"/>
    <script src=\"/static/leaflet.js\"></script>
    <script src=\"/static/leaflet.draw.js\"></script>
    """)

    def show_save_dialog(coords, edit_field=None):
        dialog = ui.dialog()
        with dialog, ui.card():
            ui.label('Сохранить поле' if edit_field else 'Сохранить новое поле').classes('text-h6 q-mb-md')
            name_input = ui.input(label='Название', value=edit_field.name if edit_field else '').classes('w-full q-mb-sm')
            group_input = ui.input(label='Группа', value=edit_field.group if edit_field else '').classes('w-full q-mb-sm')
            notes_input = ui.textarea(label='Заметки', value=edit_field.notes if edit_field else '').classes('w-full q-mb-md')

            def save():
                if not name_input.value:
                    ui.notify('Введите название', type='warning')
                    return
                session = Session()
                try:
                    if edit_field:
                        field = session.query(Field).filter(Field.id == edit_field.id, Field.user_id == ui.page.user_id).first()
                        if not field:
                            ui.notify('Поле не найдено', color='negative')
                            return
                        field.name = name_input.value
                        field.group = group_input.value
                        field.notes = notes_input.value
                        field.coordinates = json.dumps(coords)
                        field.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    else:
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
                    ui.notify('Поле успешно сохранено', color='positive')
                    dialog.close()
                    ui.open('/fields')
                except Exception as e:
                    session.rollback()
                    ui.notify(f'Ошибка при сохранении поля: {e}', color='negative')
                finally:
                    session.close()

            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                ui.button('Сохранить', on_click=save).props('color=positive')
        dialog.open()

    def on_polygon_drawn(e):
        coords = e.args['coords']
        if action == 'edit' and fields:
            session = Session()
            field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
            session.close()
            show_save_dialog(coords, edit_field=field)
        else:
            show_save_dialog(coords)

    ui.html('<div id="map" style="height: 500px;"></div>')

    js_code = """
    window.addEventListener('DOMContentLoaded', function() {
        window.sendPolygonToPython = function(coords) {
            const arr = coords[0].map(pt => ({lat: pt.lat, lng: pt.lng}));
            window.dispatchEvent(new CustomEvent('polygon_drawn', {detail: {coords: [arr]}}));
        }
        let map = L.map('map').setView([55.75, 37.62], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
        }).addTo(map);
        let drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        let drawControl = new L.Control.Draw({
            draw: {
                polygon: true,
                marker: false,
                circle: false,
                rectangle: false,
                polyline: false,
                circlemarker: false,
            },
            edit: {
                edit: false,
                remove: false,
            }
        });
        map.addControl(drawControl);
        map.on(L.Draw.Event.CREATED, function (event) {
            let layer = event.layer;
            drawnItems.addLayer(layer);
            let coords = layer.getLatLngs();
            window.sendPolygonToPython(coords);
        });
    """
    if (action in ['select', 'edit']) and fields:
        session = Session()
        field = session.query(Field).filter(Field.id == int(fields), Field.user_id == ui.page.user_id).first()
        session.close()
        if field:
            try:
                coords = json.loads(field.coordinates)
                js_code += f"\n    let polygon = L.polygon({json.dumps(coords[0])}, {{color: 'red'}}).addTo(map);\n    map.fitBounds(polygon.getBounds());"
            except Exception:
                pass
    js_code += "\n});"
    ui.run_javascript(js_code)

    ui.on('polygon_drawn', on_polygon_drawn)

    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')
