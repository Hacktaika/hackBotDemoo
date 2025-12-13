"""
Модели базы данных
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
    
    # Связи
    received_gifts = relationship("UserGift", back_populates="user", cascade="all, delete-orphan")
    
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


class Gift(Base):
    """Модель подарка/бонуса"""
    __tablename__ = 'gifts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False)  # text, photo, video, document
    text = Column(Text, nullable=True)
    file_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # Порядок отображения
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user_gifts = relationship("UserGift", back_populates="gift", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Gift(name={self.name}, order={self.order})>"


class UserGift(Base):
    """Связь пользователя и подарка"""
    __tablename__ = 'user_gifts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    gift_id = Column(Integer, ForeignKey('gifts.id', ondelete='CASCADE'), nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="received_gifts")
    gift = relationship("Gift", back_populates="user_gifts")
    
    def __repr__(self):
        return f"<UserGift(user_id={self.user_id}, gift_id={self.gift_id})>"


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

