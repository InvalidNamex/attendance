from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import Transaction, User
from schemas import TransactionResponse, TransactionUpdate
from auth import get_current_user
from ws_manager import manager
from storage import upload_photo, delete_photo
import os
import uuid

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Directory for uploaded photos
UPLOAD_DIR = "uploads"


def _normalize_photo_path(photo: Optional[str]) -> Optional[str]:
    """Return a response-safe photo URL.

    - If `photo` is None -> return None
    - If `photo` is already an absolute HTTP(S) URL -> return it unchanged
    - Otherwise ensure it starts with a single leading slash so the frontend can
      request it relative to the API base URL (e.g. `/uploads/...`).
    """
    if not photo:
        return None

    photo = photo.strip()
    # Keep full URLs (Supabase, S3, CDN, etc.) as-is
    if photo.startswith("http://") or photo.startswith("https://"):
        return photo

    # Normalize Windows backslashes and ensure a leading slash for relative paths
    photo = photo.replace("\\", "/")
    if not photo.startswith("/"):
        return f"/{photo}"
    return photo


def _transaction_to_dict(t, photo_normalized: Optional[str] = None) -> dict:
    """Convert a transaction to a JSON-serializable dict for WebSocket broadcast."""
    return {
        "id": t.id,
        "userID": t.userID,
        "timestamp": t.timestamp.isoformat(),
        "photo": photo_normalized or _normalize_photo_path(t.photo),
        "device_id": t.device_id,
        "stamp_type": t.stamp_type,
    }


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: int = Form(..., description="ID of the user for this transaction"),
    stamp_type: int = Form(..., description="0 for check-in, 1 for check-out"),
    timestamp: Optional[str] = Form(
        None, 
        description="Optional timestamp in ISO 8601 format (e.g., '2026-02-17T10:30:00'). If not provided, uses current UTC time",
        example="2026-02-17T10:30:00"
    ),
    device_id: Optional[str] = Form(None, description="Optional device id from the user's device"),
    photo: UploadFile = File(None, description="Optional photo file"),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction (check-in or check-out).
    
    **Form Fields:**
    - **user_id** (required): ID of the user for this transaction
    - **stamp_type** (required): 0 for check-in, 1 for check-out
    - **timestamp** (optional): Custom timestamp in ISO 8601 format (e.g., "2026-02-17T10:30:00"). If not provided, uses current UTC time
    - **device_id** (optional): Device id string from the user's device
    - **photo** (optional): Photo file upload
    
    **Use Cases:**
    - Leave timestamp empty for real-time check-in/out (uses current time)
    - Provide timestamp for manual/backdated entries
    - Admin corrections for missed check-ins
    """
    # Validate stamp_type
    if stamp_type not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stamp_type must be 0 (in) or 1 (out)"
        )
    
    # Parse timestamp if provided, otherwise use current time
    if timestamp:
        try:
            transaction_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid timestamp format. Use ISO 8601 format (e.g., '2026-02-17T10:30:00')"
            )
    else:
        transaction_timestamp = datetime.utcnow()
    
    # Handle photo upload if provided
    photo_url = None
    if photo:
        content = await photo.read()
        photo_url = upload_photo(content, photo.filename)
    
    # Create transaction
    new_transaction = Transaction(
        userID=user_id,
        timestamp=transaction_timestamp,
        photo=photo_url,
        device_id=device_id,
        stamp_type=stamp_type
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    response = TransactionResponse(
        id=new_transaction.id,
        userID=new_transaction.userID,
        timestamp=new_transaction.timestamp,
        photo=_normalize_photo_path(new_transaction.photo),
        device_id=new_transaction.device_id,
        stamp_type=new_transaction.stamp_type
    )

    # Broadcast INSERT to all connected WebSocket clients
    await manager.broadcast(
        event="INSERT",
        table="transactions",
        data=_transaction_to_dict(new_transaction, response.photo),
    )

    return response


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    stamp_type: Optional[int] = Query(None, description="Filter by stamp type (0=in, 1=out)"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO 8601 format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO 8601 format)"),
    db: Session = Depends(get_db)
):
    """
    Get all transactions with optional filters.
    
    Query parameters:
    - user_id: Filter by specific user
    - stamp_type: Filter by type (0=in, 1=out)
    - from_date: Start date in ISO 8601 format (e.g., 2026-02-01T00:00:00)
    - to_date: End date in ISO 8601 format (e.g., 2026-02-15T23:59:59)
    """
    query = db.query(Transaction)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(Transaction.userID == user_id)
    
    if stamp_type is not None:
        if stamp_type not in [0, 1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stamp_type must be 0 (in) or 1 (out)"
            )
        query = query.filter(Transaction.stamp_type == stamp_type)
    
    if from_date:
        try:
            from_datetime = datetime.fromisoformat(from_date)
            query = query.filter(Transaction.timestamp >= from_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid from_date format. Use ISO 8601 format (e.g., 2026-02-01T00:00:00)"
            )
    
    if to_date:
        try:
            to_datetime = datetime.fromisoformat(to_date)
            query = query.filter(Transaction.timestamp <= to_datetime)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid to_date format. Use ISO 8601 format (e.g., 2026-02-15T23:59:59)"
            )
    
    # Execute query
    transactions = query.all()
    
    return [
        TransactionResponse(
            id=transaction.id,
            userID=transaction.userID,
            timestamp=transaction.timestamp,
            photo=_normalize_photo_path(transaction.photo),
            device_id=transaction.device_id,
            stamp_type=transaction.stamp_type
        )
        for transaction in transactions
    ]


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single transaction by ID.
    
    Parameters:
    - transaction_id: ID of the transaction to retrieve
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    return TransactionResponse(
        id=transaction.id,
        userID=transaction.userID,
        timestamp=transaction.timestamp,
        photo=_normalize_photo_path(transaction.photo),
        device_id=transaction.device_id,
        stamp_type=transaction.stamp_type
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a transaction's timestamp or stamp type.
    
    Parameters:
    - transaction_id: ID of the transaction to update
    - timestamp: New timestamp (optional, ISO 8601 format)
    - stamp_type: New stamp type (optional, 0=in, 1=out)
    """
    # Find transaction
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Update fields if provided
    if update_data.timestamp is not None:
        transaction.timestamp = update_data.timestamp
    
    if update_data.stamp_type is not None:
        if update_data.stamp_type not in [0, 1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="stamp_type must be 0 (in) or 1 (out)"
            )
        transaction.stamp_type = update_data.stamp_type

    if update_data.device_id is not None:
        transaction.device_id = update_data.device_id
    
    db.commit()
    db.refresh(transaction)
    
    response = TransactionResponse(
        id=transaction.id,
        userID=transaction.userID,
        timestamp=transaction.timestamp,
        photo=_normalize_photo_path(transaction.photo),
        device_id=transaction.device_id,
        stamp_type=transaction.stamp_type
    )

    # Broadcast UPDATE to all connected WebSocket clients
    await manager.broadcast(
        event="UPDATE",
        table="transactions",
        data=_transaction_to_dict(transaction, response.photo),
    )

    return response


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a transaction.
    
    Parameters:
    - transaction_id: ID of the transaction to delete
    """
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with ID {transaction_id} not found"
        )
    
    # Delete photo from Supabase Storage if exists
    if transaction.photo:
        delete_photo(transaction.photo)
    
    transaction_id_to_broadcast = transaction.id

    db.delete(transaction)
    db.commit()

    # Broadcast DELETE to all connected WebSocket clients
    await manager.broadcast(
        event="DELETE",
        table="transactions",
        data={"id": transaction_id_to_broadcast},
    )

    return None
