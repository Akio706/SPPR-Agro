from db import Session, User
from datetime import datetime
import uuid

def authenticate_user(username, password):
    try:
        session = Session()
        user = session.query(User).filter(
            User.username == username,
            User.password == password
        ).first()
        result = None
        if user:
            user.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session.commit()
            result = {
                'user_id': user.user_id,
                'role': user.role,
                'username': user.username
            }
        session.close()
        return result
    except Exception as e:
        print(f"Ошибка при аутентификации пользователя: {e}")
        return None

def register_user(username, password, email, role='agronomist'):
    try:
        session = Session()
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            session.close()
            return False, "Пользователь с таким именем или email уже существует"
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            password=password,
            email=email,
            role=role,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(user)
        session.commit()
        session.close()
        return True, "Регистрация успешна"
    except Exception as e:
        print(f"Ошибка при регистрации пользователя: {e}")
        return False, f"Ошибка при регистрации: {str(e)}" 