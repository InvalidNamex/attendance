from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# User Schemas
class UserCreate(BaseModel):
    userName: str
    password: str
    deviceID: Optional[str] = None
    isAdmin: Optional[bool] = False


class UserUpdate(BaseModel):
    userName: Optional[str] = None
    password: Optional[str] = None
    deviceID: Optional[str] = None


class LoginRequest(BaseModel):
    userName: str
    password: str


class UserResponse(BaseModel):
    userID: int
    userName: str
    deviceID: Optional[str]
    isAdmin: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    userID: int
    userName: str
    isAdmin: bool

    class Config:
        from_attributes = True


# Settings Schemas
class SettingsUpdate(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[int] = None
    in_time: Optional[str] = None
    out_time: Optional[str] = None


class SettingsResponse(BaseModel):
    id: int
    latitude: float
    longitude: float
    radius: int
    in_time: str
    out_time: str

    class Config:
        from_attributes = True


# Transaction Schemas
class TransactionCreate(BaseModel):
    stamp_type: int  # 0 = in, 1 = out
    device_id: Optional[str] = None


class TransactionUpdate(BaseModel):
    timestamp: Optional[datetime] = None
    stamp_type: Optional[int] = None
    device_id: Optional[str] = None


class TransactionResponse(BaseModel):
    id: int
    userID: int
    timestamp: datetime
    photo: Optional[str]
    device_id: Optional[str]
    stamp_type: int

    class Config:
        from_attributes = True
