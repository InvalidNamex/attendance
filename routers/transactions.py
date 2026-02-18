from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import Transaction, User
from schemas import TransactionResponse, TransactionUpdate
from auth import get_current_user
import os
import uuid

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Directory for uploaded photos
UPLOAD_DIR = "uploads"


def _normalize_photo_path(photo: str | None) -> str | None:
    """Return a cleaned server-relative photo path.

    Robust handling for these input cases:
    - full URL(s) (http/https)
    - Windows absolute paths (C:\\.../uploads/...) or mixed separators
    - multiple values separated by whitespace, commas or semicolons

    The function always attempts to return a path starting with `uploads/` when
    possible; otherwise it returns a cleaned relative path (no leading slash).
    """
    if not photo:
        return None

    import re
    from urllib.parse import urlparse

    # Normalize separators and trim
    raw = photo.replace("\\", "/").strip()

    # Split into candidate tokens (handles space/comma/semicolon-separated values)
    tokens = [t for t in re.split(r"[\s,;]+", raw) if t]

    def _extract_from_token(tok: str) -> str | None:
        tok = tok.strip()
        if not tok:
            return None

        # If token is a full URL, return it unchanged so frontend can use it directly
        if tok.startswith("http://") or tok.startswith("https://"):
            return tok

        # Remove drive letter if present (Windows paths like C:/...)
        tok = re.sub(r'^[A-Za-z]:', '', tok)

        # Trim leading slashes
        tok = tok.lstrip('/')

        # If token contains uploads/, return the substring from uploads/
        idx = tok.find("uploads/")
        if idx != -1:
            return tok[idx:]

        # If token starts with uploads/ return it
        if tok.startswith("uploads/"):
            return tok

        # Otherwise return the cleaned token
        return tok or None

    # Prefer the first token that yields an uploads/... path
    for t in tokens:
        candidate = _extract_from_token(t)
        if candidate and candidate.startswith("uploads/"):
            return candidate

    # If none matched uploads/, return the first non-empty cleaned token
    for t in tokens:
        candidate = _extract_from_token(t)
        if candidate:
            return candidate

    return None


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: int = Form(..., description="ID of the user for this transaction"),
    stamp_type: int = Form(..., description="0 for check-in, 1 for check-out"),
    timestamp: Optional[str] = Form(
        None, 
        description="Optional timestamp in ISO 8601 format (e.g., '2026-02-17T10:30:00'). If not provided, uses current UTC time",
        example="2026-02-17T10:30:00"
    ),
    photo: UploadFile = File(None, description="Optional photo file"),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction (check-in or check-out).
    
    **Form Fields:**
    - **user_id** (required): ID of the user for this transaction
    - **stamp_type** (required): 0 for check-in, 1 for check-out
    - **timestamp** (optional): Custom timestamp in ISO 8601 format (e.g., "2026-02-17T10:30:00"). If not provided, uses current UTC time
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
    photo_path = None
    if photo:
        # Generate unique filename
        file_extension = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        # Store a normalized forward-slash path (e.g. uploads/xxxx.jpg)
        photo_path = f"{UPLOAD_DIR}/{unique_filename}"
        
        # Save file to disk (create upload dir if missing)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(photo_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
    
    # Create transaction
    new_transaction = Transaction(
        userID=user_id,
        timestamp=transaction_timestamp,
        photo=photo_path,
        stamp_type=stamp_type
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionResponse(
        id=new_transaction.id,
        userID=new_transaction.userID,
        timestamp=new_transaction.timestamp,
        photo=_normalize_photo_path(new_transaction.photo),
        stamp_type=new_transaction.stamp_type
    )


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
        stamp_type=transaction.stamp_type
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
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
    
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse(
        id=transaction.id,
        userID=transaction.userID,
        timestamp=transaction.timestamp,
        photo=_normalize_photo_path(transaction.photo),
        stamp_type=transaction.stamp_type
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
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
    
    # Delete photo file if exists
    if transaction.photo and os.path.exists(transaction.photo):
        try:
            os.remove(transaction.photo)
        except Exception as e:
            print(f"Warning: Could not delete photo file {transaction.photo}: {e}")
    
    db.delete(transaction)
    db.commit()
    
    return None
