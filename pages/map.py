from nicegui import ui
from db import Session, Field
import json
from datetime import datetime

# Add Leaflet.Draw CSS and JavaScript to the page
ui.add_head_html("""
<link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
<script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
""")

def map_page(action: str = None, fields: str = None, field_id: str = None):
    if not getattr(ui.page, 'user_id', None):
        ui.run_javascript("window.location.href = '/';")
        return

    # Create the map
    map_view = ui.leaflet(center=(55.75, 37.62), zoom=6).style('height: 500px; width: 100%;')

    # Enable polygon creation
    if action == 'create':
        ui.run_javascript(f"""
        document.addEventListener('leaflet_map_ready_{map_view.id}', function() {{
            const map = window.mapInstances['{map_view.id}'];
            if (!map) {{
                console.error('Map instance not found!');
                return;
            }}

            // Initialize the drawn items layer
            if (!window.drawnItems) {{
                window.drawnItems = new L.FeatureGroup();
                map.addLayer(window.drawnItems);
            }}

            // Add drawing controls
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

            // Handle the creation of a new polygon
            map.on(L.Draw.Event.CREATED, function (e) {{
                const layer = e.layer;
                window.drawnItems.addLayer(layer);

                // Extract coordinates
                const latlngs = layer.getLatLngs()[0].map(pt => {{ return {{ lat: pt.lat, lng: pt.lng }}; }});
                console.log('Polygon drawn with coordinates:', latlngs);

                // Send the coordinates to NiceGUI
                window.nicegui.send_event('polygon_drawn', {{ coords: [latlngs] }});
            }});
        }});
        """)

    # Dialog box to save the drawn polygon
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