from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Настройка БД
Base = declarative_base()
engine = create_engine("sqlite:///data.db")
Session = sessionmaker(bind=engine)
session = Session()

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String)
    fio = Column(String)
    phone = Column(String)
    photo_front = Column(String)
    photo_back = Column(String)

# Создание таблиц (если не созданы)
Base.metadata.create_all(engine)