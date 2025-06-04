from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
import uuid

Base = declarative_base()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/agrofields')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False, default='agronomist')
    email = Column(String, unique=True)
    created_at = Column(String, nullable=False)
    last_login = Column(String)
    markers = relationship("Marker", back_populates="user")
    polygons = relationship("Polygon", back_populates="user")
    fields = relationship("Field", back_populates="user")

class Marker(Base):
    __tablename__ = 'marker_coords'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    lat = Column(Float)
    lng = Column(Float)
    user = relationship("User", back_populates="markers")

class Polygon(Base):
    __tablename__ = 'polygon_coords'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    coords = Column(Text)
    user = relationship("User", back_populates="polygons")
    points = relationship("PolygonPoint", back_populates="polygon")

class PolygonPoint(Base):
    __tablename__ = 'polygon_coordsv2'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    lat = Column(Float)
    lng = Column(Float)
    polygon_id = Column(Integer, ForeignKey('polygon_coords.id'))
    polygon = relationship("Polygon", back_populates="points")

class Field(Base):
    __tablename__ = 'fields'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    name = Column(String, nullable=False)
    coordinates = Column(Text, nullable=False)
    area = Column(Float)
    soil_type = Column(String)
    soil_ph = Column(Float)
    humus_content = Column(String)
    soil_texture = Column(String)
    elevation = Column(Float)
    slope = Column(Float)
    aspect = Column(String)
    created_at = Column(String, nullable=False)
    last_updated = Column(String)
    group = Column(String)
    notes = Column(Text)
    custom_bonitet = Column(Float) # <--- Вот эта колонка определена в коде
    user = relationship("User", back_populates="fields")
    soil_analyses = relationship("SoilAnalysis", back_populates="field")
    climate_data = relationship("ClimateData", back_populates="field")

class SoilAnalysis(Base):
    __tablename__ = 'soil_analyses'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    analysis_date = Column(String, nullable=False)
    ph_value = Column(Float)
    humus_percentage = Column(Float)
    nitrogen_content = Column(Float)
    phosphorus_content = Column(Float)
    potassium_content = Column(Float)
    texture_class = Column(String)
    organic_matter = Column(Float)
    field = relationship("Field", back_populates="soil_analyses")

class ClimateData(Base):
    __tablename__ = 'climate_data'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    date = Column(String, nullable=False)
    temperature = Column(Float)
    precipitation = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    solar_radiation = Column(Float)
    field = relationship("Field", back_populates="climate_data")

class FieldArcGISData(Base):
    __tablename__ = 'field_arcgis_data'
    id = Column(Integer, primary_key=True)
    field_id = Column(Integer, ForeignKey('fields.id'))
    data = Column(JSON)
    created_at = Column(String, nullable=False)
    field = relationship("Field", backref="arcgis_data")

def initialize_db():
    try:
        Base.metadata.create_all(engine)
        print("База данных успешно инициализирована.")
        session = Session()
        test_username = 'Timka'
        test_email = 'testadmin@example.com'
        test_user = session.query(User).filter(
            (User.username == test_username) | (User.email == test_email)
        ).first()
        if not test_user:
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=test_username,
                password='Kolhoz',
                email=test_email,
                role='administrator',
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(user)
            session.commit()
            print(f"Тестовый пользователь '{test_username}' добавлен.")
        session.close()
    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}") 