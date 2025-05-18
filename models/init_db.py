from db import initialize_db, Session, User
from datetime import datetime
import uuid

def create_admin_user():
    """Создаем администратора, если его нет в базе"""
    session = Session()
    admin = session.query(User).filter_by(username='admin').first()
    
    if not admin:
        print("Создаем пользователя admin...")
        user_id = str(uuid.uuid4())
        admin = User(
            user_id=user_id,
            username='admin',
            password='admin123',
            email='admin@example.com',
            role='administrator',
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(admin)
        session.commit()
        print("Пользователь admin создан!")
    else:
        print("Пользователь admin уже существует")
    
    session.close()

if __name__ == '__main__':
    print("Инициализация базы данных...")
    initialize_db()
    print("База данных инициализирована!")
    
    create_admin_user()
    print("Готово!")
