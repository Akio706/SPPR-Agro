from nicegui import ui
from db import Session, Field, SoilAnalysis, ClimateData
from utils import export_all_fields_to_csv, get_arcgis_soil_params, save_arcgis_data_to_db
import json
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

    def delete_selected_fields():
        if not selected:
            ui.notify('Выберите поля для удаления', type='warning')
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Удаление {len(selected)} полей").classes('text-h6 q-mb-md')
            ui.label('Вы уверены, что хотите удалить выбранные поля? Это действие нельзя отменить.').classes('q-mb-md')
            with ui.row().classes('w-full justify-end'):
                ui.button('Отмена', on_click=dialog.close).props('flat')
                def confirm_delete():
                    any_deleted = False
                    for field in selected:
                        success, message = delete_field(field['id'], ui.page.user_id)
                        if success:
                            any_deleted = True
                        else:
                            ui.notify(message, type='negative')
                    dialog.close()
                    load_fields()
                    if any_deleted:
                        ui.notify('Поля успешно удалены', color='positive')
                ui.button('Удалить', on_click=confirm_delete).props('color=negative')

    def edit_selected():
        if not selected:
            ui.notify('Выберите поле для редактирования', type='warning')
            return
        field_id = selected[0]['id']
        ui.open(f'/map?action=edit&fields={field_id}')

    def show_field_details(field_id):
        session = Session()
        field = session.query(Field).filter(Field.id == field_id, Field.user_id == ui.page.user_id).first()
        session.close()
        if not field:
            ui.notify('Поле не найдено', color='negative')
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Детали поля: {field.name}").classes('text-h6 q-mb-md')
            ui.label(f"Создано: {field.created_at}")
            with ui.row().classes('w-full justify-end q-mt-md'):
                ui.button('Закрыть', on_click=dialog.close).props('flat')

    def load_fields():
        session = Session()
        fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
        session.close()
        result = []
        for field in fields:
            result.append({
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
            })
        fields_table.rows = result
        return result

    def filter_fields():
        session = Session()
        fields = session.query(Field).filter(Field.user_id == ui.page.user_id).all()
        session.close()
        if search_text.value:
            filtered = [f for f in fields if search_text.value.lower() in f.name.lower()]
        else:
            filtered = fields
        result = []
        for field in filtered:
            result.append({
                'id': field.id,
                'name': field.name,
                'created_at': field.created_at,
            })
        fields_table.rows = result

    with ui.column().classes('items-center justify-center min-h-screen bg-grey-2'):
        with ui.card().classes('w-full max-w-4xl shadow-lg mt-8'):
            ui.label('Управление полями').classes('text-h4 q-mb-md text-center')
            with ui.row().classes('q-mb-md justify-center'):
                ui.button('Создать новое поле', on_click=lambda: ui.open('/map?action=create')).props('color=positive').classes('q-mr-md')
                ui.button('Удалить выбранные', on_click=delete_selected_fields).props('color=negative').classes('q-mr-md')
                ui.button('Редактировать выбранное', on_click=edit_selected).props('color=primary').classes('q-mr-md')
            with ui.row().classes('q-mb-md justify-center'):
                search_text = ui.input(label='Поиск по названию').classes('q-mr-md')
                search_text.on('change', filter_fields)
                ui.button('Экспортировать в CSV', on_click=lambda: export_all_fields_to_csv(ui.page.user_id, f'fields_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')).props('color=secondary')
            fields_table = ui.table(
                columns=[
                    {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                    {'name': 'name', 'label': 'Название', 'field': 'name', 'align': 'left'},
                    {'name': 'created_at', 'label': 'Создано', 'field': 'created_at', 'align': 'left'},
                ],
                rows=[],
                row_key='id',
                selection='multiple',
                on_select=on_select
            ).classes('w-full')
            ui.button('Показать детали выбранного', on_click=lambda: show_field_details(selected[0]['id']) if selected else ui.notify('Выберите поле', type='warning')).props('color=info').classes('mt-2')
            ui.button('Назад к карте', on_click=lambda: ui.open('/map')).props('color=secondary').classes('mt-4')
    load_fields()

def delete_field(field_id, user_id):
    try:
        session = Session()
        field = session.query(Field).filter(
            Field.id == field_id,
            Field.user_id == user_id
        ).first()
        if not field:
            return False, "Поле не найдено"
        session.query(SoilAnalysis).filter(SoilAnalysis.field_id == field_id).delete()
        session.query(ClimateData).filter(ClimateData.field_id == field_id).delete()
        session.delete(field)
        session.commit()
        return True, "Поле успешно удалено"
    except Exception as e:
        print(f"Ошибка при удалении поля: {e}")
        session.rollback()
        return False, f"Ошибка при удалении поля: {str(e)}"
    finally:
        session.close() 