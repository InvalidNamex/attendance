from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from zoneinfo import available_timezones
from database import get_db
from models import Settings, User
from schemas import SettingsUpdate, SettingsResponse
from auth import get_current_user, get_admin_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get global settings (Authenticated users).
    Returns location parameters and time settings.
    """
    settings = db.query(Settings).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not configured"
        )
    
    return SettingsResponse(
        id=settings.id,
        latitude=settings.latitude,
        longitude=settings.longitude,
        radius=settings.radius,
        in_time=settings.in_time,
        out_time=settings.out_time,
        timezone=settings.timezone
    )


@router.get("/timezones", response_model=List[str])
def get_timezones(
    current_user: User = Depends(get_current_user)
):
    """
    Get all available IANA timezone names (Authenticated users).
    Returns a sorted list for populating a searchable dropdown.
    """
    return sorted(available_timezones())


@router.put("/", response_model=SettingsResponse)
def update_settings(
    settings_data: SettingsUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Update global settings (Admin only).
    Modifies location parameters, radius, and time settings.
    """
    settings = db.query(Settings).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not configured"
        )
    
    # Update fields if provided
    if settings_data.latitude is not None:
        settings.latitude = settings_data.latitude
    
    if settings_data.longitude is not None:
        settings.longitude = settings_data.longitude
    
    if settings_data.radius is not None:
        settings.radius = settings_data.radius
    
    if settings_data.in_time is not None:
        settings.in_time = settings_data.in_time
    
    if settings_data.out_time is not None:
        settings.out_time = settings_data.out_time
    
    if settings_data.timezone is not None:
        if settings_data.timezone not in available_timezones():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone '{settings_data.timezone}'. Use GET /settings/timezones for valid options."
            )
        settings.timezone = settings_data.timezone
    
    db.commit()
    db.refresh(settings)
    
    return SettingsResponse(
        id=settings.id,
        latitude=settings.latitude,
        longitude=settings.longitude,
        radius=settings.radius,
        in_time=settings.in_time,
        out_time=settings.out_time,
        timezone=settings.timezone
    )
