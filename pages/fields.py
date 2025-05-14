from nicegui import ui
from db import Session, Field
from datetime import datetime

def fields_page():
    if not getattr(ui.page, 'user_id', None):
        return ui.open('/')
    selected = []

    def logout():
        ui.page.user_id = None
        ui.page.user_role = None
        ui.notify('Вы вышли из аккаунта', type='positive')
        ui.open('/')

    with ui.row().classes('absolute top-0 right-0 z-50 p-4'):
        ui.button('Выйти', on_click=logout).props('color=negative').classes('q-ml-md')

    def on_select(e):
        selected.clear()
        if hasattr(e, 'selected') and e.selected:
            selected.extend(e.selected)

    def edit_selected():
        if not selected:
            ui.notify('Выберите поле для редактирования', type='warning')
            return
        field_id = selected[0]['id']
        ui.open(f'/map?action=edit&fields={field_id}')

    session = Session()
    fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
    session.close()
    rows = []
    for field in fields:
        rows.append({
            'id': field.id,
            'name': field.name,
            'created_at': field.created_at,
        })

    with ui.card().classes('w-full max-w-3xl mx-auto mt-8'):
        ui.label('Список полей').classes('text-h5 q-mb-md')
        fields_table = ui.table(
            columns=[
                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
                {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'},
            ],
            rows=rows,
            row_key='id',
            selection='single',
            on_select=on_select
        ).classes('w-full')
        ui.button('Редактировать выбранное поле', on_click=edit_selected).props('color=primary').classes('mt-2') 