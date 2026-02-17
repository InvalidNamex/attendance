from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from database import get_db
from models import Transaction, User
from schemas import TransactionResponse
from auth import get_current_user
import os
import uuid

router = APIRouter(prefix="/transactions", tags=["transactions"])

# Directory for uploaded photos
UPLOAD_DIR = "uploads"


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    user_id: int = Form(...),
    stamp_type: int = Form(...),
    photo: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction (check-in or check-out).
    
    Parameters:
    - user_id: ID of the user for this transaction
    - stamp_type: 0 for check-in, 1 for check-out
    - photo: Optional photo file upload
    """
    # Validate stamp_type
    if stamp_type not in [0, 1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stamp_type must be 0 (in) or 1 (out)"
        )
    
    # Handle photo upload if provided
    photo_path = None
    if photo:
        # Generate unique filename
        file_extension = os.path.splitext(photo.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        photo_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(photo_path, "wb") as buffer:
            content = await photo.read()
            buffer.write(content)
    
    # Create transaction
    new_transaction = Transaction(
        userID=user_id,
        timestamp=datetime.utcnow(),
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
        photo=new_transaction.photo,
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
            photo=transaction.photo,
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
        photo=transaction.photo,
        stamp_type=transaction.stamp_type
    )
