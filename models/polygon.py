from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from models.database import Base
from datetime import datetime
import bcrypt

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    polygons = relationship("Polygon", back_populates="user")
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

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
