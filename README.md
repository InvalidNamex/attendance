# Attendance API - FastAPI + PostgreSQL

A complete attendance tracking system with location-based check-in/out, photo capture, HTTP Basic Authentication, and admin controls.

## Features

- ✅ FastAPI with automatic OpenAPI documentation
- ✅ PostgreSQL database (Supabase) with SQLAlchemy ORM
- ✅ HTTP Basic Authentication on all endpoints
- ✅ Bcrypt password hashing
- ✅ Role-based access control (Admin/User)
- ✅ Photo uploads for transactions
- ✅ Location-based settings (latitude, longitude, radius)
- ✅ Transaction filtering by date range, user, and type
- ✅ Environment variable configuration
- ✅ Production-ready deployment (Render, PythonAnywhere)

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── database.py             # Database connection & initialization
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic request/response models
├── auth.py                 # Basic auth & password hashing
├── routers/                # API route handlers
│   ├── users.py           # User management endpoints
│   ├── settings.py        # Settings endpoints
│   └── transactions.py    # Transaction endpoints
├── uploads/                # Photo storage directory
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
├── render.yaml             # Render deployment config
└── DEPLOYMENT.md          # Deployment guides
```

## Installation

### 1. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure environment variables:

Copy `.env.example` to `.env` and fill in your Supabase credentials:

```env
user=postgres.YOUR_PROJECT_REF
password=YOUR_SUPABASE_PASSWORD
host=aws-X-region.pooler.supabase.com
port=6543
dbname=postgres
```

### 3. Run the server:
```bash
uvicorn main:app --reload
```

The database tables will be created automatically on first run.

### 4. Access the API:
- API: http://localhost:8000
- OpenAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Credentials

On first startup, a bootstrap admin user is created:
- **Username:** `admin`
- **Password:** `admin123`

⚠️ **IMPORTANT:** Change the default password immediately using the update user endpoint!

## Database Schema

### Users Table
- `id` - Primary key (auto-increment)
- `userName` - Unique username
- `password` - Bcrypt hashed password
- `deviceID` - Optional device identifier
- `isAdmin` - Admin flag (boolean)

### Settings Table
- `id` - Primary key
- `latitude` - Location latitude
- `longitude` - Location longitude
- `radius` - Allowed check-in radius (meters)
- `in_time` - Expected check-in time (e.g., "09:00")
- `out_time` - Expected check-out time (e.g., "17:00")

### Transactions Table
- `id` - Primary key (auto-increment)
- `userID` - Foreign key to users
- `timestamp` - Transaction timestamp (UTC)
- `photo` - File path to uploaded photo
- `stamp_type` - 0 = check-in, 1 = check-out

## API Endpoints

### User Endpoints

#### POST /users/
Create a new user (Admin only)
```json
{
  "userName": "string",
  "password": "string",
  "deviceID": "string",
  "isAdmin": false
}
```

#### POST /users/login
Login with Basic Auth credentials
- Returns: `{userID, userName, isAdmin}`

#### GET /users/
Get all users (Authenticated)

#### PUT /users/{userID}
Update user (Users can update self, admins can update any)
```json
{
  "userName": "string",
  "password": "string",
  "deviceID": "string"
}
```

#### DELETE /users/{userID}
Delete user (Admin only)

### Settings Endpoints

#### GET /settings/
Get global settings (Authenticated)

#### PUT /settings/
Update settings (Admin only)
```json
{
  "latitude": 0.0,
  "longitude": 0.0,
  "radius": 100,
  "in_time": "09:00",
  "out_time": "17:00"
}
```

### Transaction Endpoints

#### POST /transactions/
Create transaction with photo upload
- Form data:
  - `stamp_type`: 0 (check-in) or 1 (check-out)
  - `photo`: File upload (optional)

#### GET /transactions/
Get all transactions with optional filters
- Query parameters:
  - `user_id`: Filter by user ID
  - `stamp_type`: Filter by type (0 or 1)
  - `from_date`: Start date (ISO 8601 format)
  - `to_date`: End date (ISO 8601 format)

Example: `/transactions/?user_id=1&stamp_type=0&from_date=2026-02-01T00:00:00&to_date=2026-02-15T23:59:59`

## Authentication

All endpoints require HTTP Basic Authentication:
```bash
curl -u username:password http://localhost:8000/users/login
```

## Permissions

- **Authenticated Users:** Can view users, settings, transactions; create transactions; update own profile
- **Admins Only:** Create/delete users, update settings

## Development

To run in development mode with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testing with cURL

Login:
```bash
curl -u admin:admin123 http://localhost:8000/users/login
```

Create user (admin only):
```bash
curl -u admin:admin123 -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"userName":"john","password":"pass123","isAdmin":false}'
```

Create transaction with photo:
```bash
curl -u john:pass123 -X POST http://localhost:8000/transactions/ \
  -F "stamp_type=0" \
  -F "photo=@photo.jpg"
```

Get transactions:
```bash
curl -u john:pass123 "http://localhost:8000/transactions/?user_id=2&stamp_type=0"
```
