from nicegui import ui
from db import Session, Field
import json
from utils import polygon_area_ha

def yield_page():
    ui.label('Расчёт урожая').classes('text-h5 q-mb-md')
    session = Session()
    fields = session.query(Field).all()
    session.close()
    field_options = [(f"{field.id}: {field.name}", field.id) for field in fields]
    selected_field = ui.select(options=field_options, label='Выберите поле').classes('q-mb-md')
    area_input = ui.input(label='Площадь поля (га)').props('type=number').classes('q-mb-md')
    yield_input = ui.input(label='Урожайность (ц/га)').props('type=number').classes('q-mb-md')
    result_label = ui.label('').classes('text-h6 q-mt-md')
    map_view = ui.leaflet(center=[55.75, 37.61], zoom=10).classes('w-full h-96')

    def on_field_change(e):
        field_id = selected_field.value
        if not field_id:
            return
        session = Session()
        field = session.query(Field).filter(Field.id == field_id).first()
        session.close()
        if not field:
            return
        # Автозаполнение площади
        area = field.area
        coords = json.loads(field.coordinates)
        if not area or area == 0:
            area = polygon_area_ha(coords)
        area_input.value = f'{area:.2f}'
        # Отрисовка контура на карте
        map_view.clear()
        map_view.polygon(coords, color='green')
        if coords and len(coords) > 0:
            lat = sum(p[0] for p in coords) / len(coords)
            lng = sum(p[1] for p in coords) / len(coords)
            map_view.set_center((lat, lng))

    selected_field.on('update:model-value', on_field_change)

    def calculate():
        try:
            area = float(area_input.value)
            yield_per_ha = float(yield_input.value)
            total = area * yield_per_ha
            result_label.text = f'Ожидаемый урожай: {total:.2f} центнеров'
        except Exception:
            result_label.text = 'Проверьте введённые значения.'
    ui.button('Рассчитать', on_click=calculate).props('color=primary')

ui.page('/yield')(yield_page) 