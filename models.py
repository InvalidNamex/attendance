from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userName = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)  # Will store hashed password
    deviceID = Column(String, nullable=True)
    isAdmin = Column(Boolean, default=False, nullable=False)

    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Integer, default=0, nullable=False)
    in_time = Column(String, nullable=False)  # e.g., "09:00"
    out_time = Column(String, nullable=False)  # e.g., "17:00"
    timezone = Column(String, default="UTC", nullable=False)  # IANA timezone name


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userID = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    photo = Column(String, nullable=True)  # File path to photo
    device_id = Column(String, nullable=True)  # Device id sent by user's device
    stamp_type = Column(Integer, nullable=False)  # 0 = in, 1 = out

    # Relationship to user
    user = relationship("User", back_populates="transactions")
