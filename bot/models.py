from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True) # Telegram ID
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=False)
    role = Column(String, default='supporter') # supporter, expert, admin
    phone = Column(String, nullable=True)
    expertise = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    supporters_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

class Vote(Base):
    __tablename__ = 'votes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    voter_id = Column(Integer, ForeignKey('users.id'))
    expert_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
