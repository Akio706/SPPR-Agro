from nicegui import ui
from db import Session, Field
import json
from datetime import datetime

# Подключаем Leaflet и Leaflet Draw (CSS и JS)
ui.add_head_html("""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.7/dist/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet-draw@1.0.7/dist/leaflet.draw.js"></script>
""")

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
                    user_id=1,  # Замените на актуального пользователя
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
    show_save_dialog(coords)

ui.html('<div id="map" style="height: 500px;"></div>')

ui.add_body_html("""
<script>
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
    // Отправляем координаты в Python
    window.sendPolygonToPython(coords);
});
</script>
""")

ui.run_javascript("""
window.sendPolygonToPython = function(coords) {
    // Преобразуем координаты в массив для передачи
    const arr = coords[0].map(pt => [pt.lat, pt.lng]);
    window.dispatchEvent(new CustomEvent('polygon_drawn', {detail: {coords: arr}}));
}
""")

ui.on_event('polygon_drawn', on_polygon_drawn)

ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')

# Запускаем приложение
ui.run()
