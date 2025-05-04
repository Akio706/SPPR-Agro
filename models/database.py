from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Используйте тот же URL, что и в вашем текущем приложении
DATABASE_URL = "sqlite:///./geo_app.db"  # или другой URL для вашей базы

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def init_db():
    # Импортируем модели для создания таблиц
    from models.polygon import Polygon, PolygonPoint, User
    Base.metadata.create_all(engine)
