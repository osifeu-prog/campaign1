import os
from sqlalchemy import create_all, create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, User, Position

# ב-Railway תקבל DATABASE_URL אוטומטית
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dbname")
if DATABASE_URL.startswith("postgres://"): # תיקון פורמט עבור SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DBService:
    def __init__(self):
        Base.metadata.create_all(bind=engine)

    def get_db(self):
        db = SessionLocal()
        try:
            return db
        finally:
            db.close()

    def get_user(self, user_id: int):
        with SessionLocal() as session:
            return session.query(User).filter(User.id == user_id).first()

    def add_user(self, user_data: dict):
        with SessionLocal() as session:
            user = User(**user_data)
            session.merge(user) # יוצר חדש או מעדכן קיים
            session.commit()

    def get_all_experts(self, only_approved=True):
        with SessionLocal() as session:
            query = session.query(User).filter(User.role == 'expert')
            if only_approved:
                query = query.filter(User.is_approved == True)
            return query.all()

    def increment_support(self, expert_id: int):
        with SessionLocal() as session:
            expert = session.query(User).filter(User.id == expert_id).first()
            if expert:
                expert.supporters_count += 1
                session.commit()
                return True
            return False
