from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse, LoginResponse, LoginRequest
from auth import get_current_user, get_admin_user, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Create a new user (Admin only).
    Password will be hashed before storing.
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.userName == user_data.userName).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user with hashed password
    new_user = User(
        userName=user_data.userName,
        password=hash_password(user_data.password),
        deviceID=user_data.deviceID,
        isAdmin=user_data.isAdmin
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        userID=new_user.id,
        userName=new_user.userName,
        deviceID=new_user.deviceID,
        isAdmin=new_user.isAdmin
    )


@router.post("/login", response_model=LoginResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login endpoint - validates credentials from JSON body.
    Returns user information on successful authentication.
    """
    # Find user by username
    user = db.query(User).filter(User.userName == login_data.userName).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return LoginResponse(
        userID=user.id,
        userName=user.userName,
        isAdmin=user.isAdmin
    )


@router.get("/", response_model=List[UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all users (Authenticated users).
    Password is excluded from response.
    """
    users = db.query(User).all()
    
    return [
        UserResponse(
            userID=user.id,
            userName=user.userName,
            deviceID=user.deviceID,
            isAdmin=user.isAdmin
        )
        for user in users
    ]


@router.put("/{userID}", response_model=UserResponse)
def update_user(
    userID: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information.
    Users can update their own profile, admins can update any user.
    """
    # Get target user
    user = db.query(User).filter(User.id == userID).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions: user can only update themselves unless admin
    if current_user.id != userID and not current_user.isAdmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Update fields if provided
    if user_data.userName is not None:
        # Check if new username already exists
        existing = db.query(User).filter(
            User.userName == user_data.userName,
            User.id != userID
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        user.userName = user_data.userName
    
    if user_data.password is not None:
        user.password = hash_password(user_data.password)
    
    if user_data.deviceID is not None:
        user.deviceID = user_data.deviceID
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        userID=user.id,
        userName=user.userName,
        deviceID=user.deviceID,
        isAdmin=user.isAdmin
    )


@router.delete("/{userID}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    userID: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Delete a user (Admin only).
    Admin users cannot be deleted.
    """
    user = db.query(User).filter(User.id == userID).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deletion of admin users
    if user.isAdmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )
    
    db.delete(user)
    db.commit()
    
    return None
