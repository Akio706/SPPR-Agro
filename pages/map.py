from nicegui import ui, events
from db import Session, Field
import json
from datetime import datetime

def normalize_coords(coords):
    if not coords or not isinstance(coords, list):
        return []
    if isinstance(coords[0], list):
        return [item for sub in coords for item in normalize_coords(sub)]
    if isinstance(coords[0], dict):
        return [[float(p['lat']), float(p['lng'])] for p in coords if 'lat' in p and 'lng' in p]
    if isinstance(coords[0], (tuple, list)) and len(coords[0]) == 2:
        return [[float(p[0]), float(p[1])] for p in coords]
    return []

def get_all_fields(user_id):
    with Session() as session:
        fields = session.query(Field).filter(Field.user_id == user_id).all()
        return fields

def handle_draw(e: events.GenericEventArguments):
    user_id = getattr(ui.page, 'user_id', None)
    if not user_id:
        ui.notify('Необходима авторизация', color='negative')
        return
    coords = e.args['layer']['_latlngs']
    coords_json = json.dumps(coords)
    with Session() as session:
        field = Field(
            user_id=user_id,
            name=f'Поле {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            coordinates=coords_json,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(field)
        session.commit()
    ui.notify('Полигон сохранён в базе', color='positive')
    ui.open('/map')

def show_all_polygons(m, user_id):
    fields = get_all_fields(user_id)
    for field in fields:
        try:
            coords = json.loads(field.coordinates)
            coords = normalize_coords(coords)
            if coords and len(coords) >= 3:
                m.generic_layer(name=f'polygon_{field.id}', args=[coords, {'color': 'blue', 'weight': 2}])
        except Exception:
            continue

def map_page(action: str = None, fields: str = None, field_id: str = None):
    user_id = getattr(ui.page, 'user_id', None)
    if not user_id:
        ui.label('Необходима авторизация').classes('text-h6 q-mb-md')
        return
    params = ui.query()
    action = action or (params.get('action') if params else None)
    fields = fields or (params.get('fields') if params else None)
    field_id = field_id or (params.get('field_id') if params else None)
    draw_control = {
        'draw': {
            'polygon': True if action == 'create' else False,
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
    m = ui.leaflet(center=(55.75, 37.62), zoom=9, draw_control=draw_control).classes('h-96 w-full')
    show_all_polygons(m, user_id)
    if action == 'create':
        m.on('draw:created', handle_draw)
    ui.button('Назад', on_click=lambda: ui.run_javascript('window.history.back()')).props('flat color=primary').classes('mb-4')
    ui.button('Назад к полям', on_click=lambda: ui.open('/fields')).classes('mt-4')

ui.page('/map')(map_page)