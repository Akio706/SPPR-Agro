from db import initialize_db, Session, User
from datetime import datetime
import uuid
import geopandas as gpd
from sqlalchemy import create_engine
import os

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

def import_soil_regions():
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/frostdb')
    engine = create_engine(DATABASE_URL)
    gdf = gpd.read_file('soil_regions.gpkg')
    gdf.to_postgis('soil_regions', engine, if_exists='replace', index=False)

def import_soils():
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/frostdb')
    engine = create_engine(DATABASE_URL)
    gdf = gpd.read_file('soil_regions_full.gpkg')
    gdf.to_postgis('soils', engine, if_exists='replace', index=False)

if __name__ == '__main__':
    print("Инициализация базы данных...")
    initialize_db()
    print("База данных инициализирована!")
    
    create_admin_user()
    print("Готово!")
    print("Импорт soil_regions.gpkg...")
    import_soil_regions()
    print("Импорт soil_regions.gpkg завершён!")
    print("Импорт soil_regions_full.gpkg...")
    import_soils()
    print("Импорт soil_regions_full.gpkg завершён!")
