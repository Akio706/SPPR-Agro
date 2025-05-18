from nicegui import ui
from auth import authenticate_user, register_user

def main_page():
    def login(username, password):
        if not username or not password:
            ui.notify('Имя пользователя и пароль не могут быть пустыми', type='warning')
            return
        user = authenticate_user(username, password)
        if user:
            ui.page.user_id = user['user_id']
            ui.page.user_role = user['role']
            ui.notify(f'Добро пожаловать, {username}!', type='positive')
            ui.open('/fields')
        else:
            ui.notify('Неверное имя пользователя или пароль', type='negative')

    def register(username, password, email):
        if not username or not password or not email:
            ui.notify('Все поля должны быть заполнены', type='warning')
            return
        if len(password) < 8:
            ui.notify('Пароль должен содержать минимум 8 символов', type='warning')
            return
        success, message = register_user(username, password, email)
        if success:
            ui.notify(message, type='positive')
        else:
            ui.notify(message, type='negative')

    with ui.card().classes('w-96 mx-auto mt-20'):
        ui.label('Вход в систему').classes('text-h4 q-mb-md')
        with ui.tabs().classes('w-full') as tabs:
            ui.tab('Вход')
            ui.tab('Регистрация')
        with ui.tab_panels(tabs, value='Вход').classes('w-full'):
            with ui.tab_panel('Вход'):
                login_username = ui.input(label='Имя пользователя').classes('w-full q-mb-md')
                login_password = ui.input(label='Пароль', password=True).classes('w-full q-mb-md')
                ui.button('Войти', on_click=lambda: login(login_username.value, login_password.value)).classes('w-full')
            with ui.tab_panel('Регистрация'):
                with ui.form(on_submit=lambda: register(reg_username.value, reg_password.value, reg_email.value)):
                    reg_username = ui.input(label='Имя пользователя').classes('w-full q-mb-md')
                    reg_email = ui.input(label='Email').classes('w-full q-mb-md')
                    reg_password = ui.input(label='Пароль', password=True).classes('w-full q-mb-md')
                    ui.button('Зарегистрироваться', type='submit').classes('w-full')

    # Кнопка выхода не нужна на странице авторизации! 