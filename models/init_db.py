from models.database import init_db, Session
from models.polygon import User

def create_admin_user():
    """Создаем администратора, если его нет в базе"""
    session = Session()
    admin = session.query(User).filter_by(username='admin').first()
    
    if not admin:
        print("Создаем пользователя admin...")
        admin = User(username='admin')
        admin.set_password('admin123')  # В реальном проекте используйте сложный пароль!
        session.add(admin)
        session.commit()
        print("Пользователь admin создан!")
    else:
        print("Пользователь admin уже существует")
    
    session.close()

if __name__ == '__main__':
    print("Инициализация базы данных...")
    init_db()
    print("База данных инициализирована!")
    
    create_admin_user()
    print("Готово!")
