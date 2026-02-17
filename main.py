from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import create_tables, SessionLocal
from models import User, Settings
from auth import hash_password
from routers import users, settings, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database tables and creates default data.
    """
    # Startup
    print("Starting up...")
    
    # Create all database tables
    create_tables()
    print("Database tables created")
    
    # Initialize default data
    db = SessionLocal()
    try:
        # Create default settings if not exists
        existing_settings = db.query(Settings).first()
        if not existing_settings:
            default_settings = Settings(
                latitude=0.0,
                longitude=0.0,
                radius=100,
                in_time="09:00",
                out_time="17:00"
            )
            db.add(default_settings)
            db.commit()
            print("Default settings created")
        
        # Create bootstrap admin user if no users exist
        existing_users = db.query(User).count()
        if existing_users == 0:
            admin_user = User(
                userName="admin",
                password=hash_password("admin123"),
                deviceID=None,
                isAdmin=True
            )
            db.add(admin_user)
            db.commit()
            print("Bootstrap admin user created (username: admin, password: admin123)")
            print("⚠️  IMPORTANT: Change the default admin password immediately!")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Attendance API",
    description="FastAPI + SQLite attendance tracking system with location-based check-in/out",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins - restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(users.router)
app.include_router(settings.router)
app.include_router(transactions.router)


@app.get("/", tags=["root"])
def root():
    """Root endpoint - API health check"""
    return {
        "message": "Attendance API is running",
        "docs": "/docs",
        "redoc": "/redoc"
    }
