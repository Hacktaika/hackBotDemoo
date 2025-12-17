"""
Модели базы данных
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Данные опросника
    name = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    expectations = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)  # соцсети, сарафанка, сайт, другие
    
    # Статусы
    is_registered = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    has_bonus = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Админ
    is_admin = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Content(Base):
    """Модель контента (для отправки по ключевому слову)"""
    __tablename__ = 'content'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(255), unique=True, nullable=False, index=True)
    content_type = Column(String(50), nullable=False)  # text, photo, video, document
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)  # ID файла в Telegram
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Content(keyword={self.keyword}, type={self.content_type})>"


class InfoPage(Base):
    """Информационные страницы (ХакТайка, Основатель)"""
    __tablename__ = 'info_pages'
    
    id = Column(Integer, primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # hacktaika, founder
    title = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    photo_file_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<InfoPage(slug={self.slug}, title={self.title})>"


class Broadcast(Base):
    """История рассылок"""
    __tablename__ = 'broadcasts'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, nullable=False)
    content_type = Column(String(50), nullable=False)
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Broadcast(id={self.id}, sent={self.sent_count})>"
