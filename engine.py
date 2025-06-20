from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# Настройка БД
Base = declarative_base()
engine = create_engine("sqlite:///data.db")
Session = sessionmaker(bind=engine)
session = Session()

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)
    fio = Column(String)
    phone = Column(String)
    photo_front = Column(String)
    photo_back = Column(String)
    region = Column(String)
    license_type = Column(String)
    

    services = relationship("UserService", back_populates="user", cascade="all, delete-orphan")

class UserService(Base):
    __tablename__ = "user_services"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_name = Column(String)

    user = relationship("User", back_populates="services")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    tg_id = Column(String, unique=True)
    
    

# Создание таблиц (если не созданы)
Base.metadata.create_all(engine)


import random

def get_user_without_service(service_name: str):
    users = session.query(User).all()
    eligible_users = [
        user for user in users
        if service_name not in [s.service_name for s in user.services]
        and len(user.services) < 4
    ]
    if not eligible_users:
        return None
    return random.choice(eligible_users)


def assign_service_to_user(user: User, service_name: str):
    # Проверка: вдруг уже назначено
    if service_name in [s.service_name for s in user.services]:
        return False

    new_service = UserService(user_id=user.id, service_name=service_name)
    session.add(new_service)
    session.commit()
    return True


def get_admin(tg_id):
    result = session.query(Admin).filter(Admin.tg_id == tg_id).first()
    if result:
        return result
    else:
        return None
    

def add_admin(tg_id):
    new_admin = Admin(tg_id=tg_id)
    session.add(new_admin)
    session.commit()

def get_random_user():
    users = session.query(User).filter(
        (User.service_number == None) | (User.service_number == "")
    ).all()
    if not users:
        return None
    return random.choice(users)
