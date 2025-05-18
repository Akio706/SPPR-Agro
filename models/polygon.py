from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
#from models.database import Base  # Удаляем, чтобы не было конфликтов
#from datetime import datetime
#import bcrypt

# Удаляем дублирующую модель User и методы set_password/check_password

# Если нужны Polygon и PolygonPoint, их можно оставить, но использовать Base из db.py при необходимости
# class Polygon(Base): ...
# class PolygonPoint(Base): ...

class Polygon(Base):
    __tablename__ = 'polygons'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="polygons")
    points = relationship("PolygonPoint", back_populates="polygon")

class PolygonPoint(Base):
    __tablename__ = 'polygon_points'
    
    id = Column(Integer, primary_key=True)
    polygon_id = Column(Integer, ForeignKey('polygons.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    order = Column(Integer, nullable=True)
    
    polygon = relationship("Polygon", back_populates="points")
