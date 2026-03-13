from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.engine import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)   # set after contact shared
    balance = Column(Float, default=0.0)
    total_spent = Column(Float, default=0.0)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    keys = relationship("Key", back_populates="user")

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    
    purchases = relationship("Purchase", back_populates="product")
    keys = relationship("Key", back_populates="product")

class Key(Base):
    __tablename__ = 'keys'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    key_value = Column(String, unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    used_by = Column(BigInteger, ForeignKey('users.tg_id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    product = relationship("Product", back_populates="keys")
    user = relationship("User", back_populates="keys", foreign_keys=[used_by])
    purchase = relationship("Purchase", back_populates="key", uselist=False)

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True, index=True)
    user_tg_id = Column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    key_id = Column(Integer, ForeignKey('keys.id'), nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")
    key = relationship("Key", back_populates="purchase", foreign_keys=[key_id])

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, index=True)
    user_tg_id = Column(BigInteger, ForeignKey('users.tg_id'), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # pending, approved, rejected
    receipt_file_id = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="payments")
