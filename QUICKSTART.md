# Attendance API - Quick Start Guide

## ✅ Installation Complete!

Your FastAPI attendance tracking system is fully implemented and tested.

## 🚀 What's Been Created

### Project Files
- **main.py** - FastAPI application with startup initialization
- **database.py** - SQLAlchemy database configuration
- **models.py** - Database ORM models (User, Settings, Transaction)
- **schemas.py** - Pydantic request/response models
- **auth.py** - HTTP Basic Auth with bcrypt password hashing
- **routers/** - API endpoints (users, settings, transactions)
- **test_api.py** - Comprehensive test suite
- **requirements.txt** - Python dependencies
- **README.md** - Full documentation

### Database Schema
- **Users**: id, userName, password (hashed), deviceID, isAdmin
- **Settings**: latitude, longitude, radius, in_time, out_time
- **Transactions**: userID, timestamp, photo, stamp_type (0=in, 1=out)

## 🔐 Default Admin Credentials

```
Username: admin
Password: admin123
```

**⚠️ IMPORTANT:** Change this password immediately after setup!

## 🏃 Running the Server

The server is currently running at:
- **API**: http://127.0.0.1:8000
- **OpenAPI Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

To start it again in the future:
```powershell
D:/attendance/backend/.venv/Scripts/python.exe -m uvicorn main:app --reload
```

## 📋 API Endpoints

### User Endpoints
- `POST /users/` - Create user (admin only)
- `POST /users/login` - Login with Basic Auth
- `GET /users/` - List all users
- `PUT /users/{userID}` - Update user
- `DELETE /users/{userID}` - Delete user (admin only)

### Settings Endpoints
- `GET /settings/` - Get global settings
- `PUT /settings/` - Update settings (admin only)

### Transaction Endpoints
- `POST /transactions/` - Create transaction with optional photo
- `GET /transactions/` - List transactions (with filters)

## 🧪 Test Results

All endpoints tested successfully:
- ✅ Root endpoint
- ✅ Admin login
- ✅ Get settings
- ✅ Create user
- ✅ Get all users
- ✅ Update settings
- ✅ Create transaction
- ✅ Get transactions
- ✅ Unauthorized access (401)

## 📝 Example Usage

### Login
```bash
curl -u admin:admin123 http://localhost:8000/users/login
```

### Create User (Admin)
```bash
curl -u admin:admin123 -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"userName":"john","password":"pass123","deviceID":"device001"}'
```

### Create Transaction (Check-in)
```bash
curl -u john:pass123 -X POST http://localhost:8000/transactions/ \
  -F "stamp_type=0" \
  -F "photo=@/path/to/photo.jpg"
```

### Get Transactions (Filtered)
```bash
curl -u admin:admin123 "http://localhost:8000/transactions/?user_id=2&stamp_type=0&from_date=2026-02-01T00:00:00&to_date=2026-02-15T23:59:59"
```

### Update Settings (Admin)
```bash
curl -u admin:admin123 -X PUT http://localhost:8000/settings/ \
  -H "Content-Type: application/json" \
  -d '{"latitude":37.7749,"longitude":-122.4194,"radius":200,"in_time":"08:30","out_time":"17:30"}'
```

## 🔒 Security Features

- ✅ HTTP Basic Authentication on all endpoints
- ✅ Bcrypt password hashing (never stores plain text)
- ✅ Role-based access control (Admin/User privileges)
- ✅ Input validation with Pydantic models
- ✅ SQL injection protection via SQLAlchemy ORM

## 📦 Dependencies Installed

- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- sqlalchemy==2.0.36
- passlib==1.7.4
- bcrypt==3.2.2
- python-multipart==0.0.6

## 🎯 Next Steps

1. **Change admin password** via `/users/1` endpoint
2. **Configure settings** with your location coordinates
3. **Create users** for your team
4. **Test photo uploads** with transaction creation
5. **Review OpenAPI docs** at http://127.0.0.1:8000/docs
6. **Run automated tests** with `python test_api.py`

## 📚 Documentation

See [README.md](README.md) for complete API documentation and examples.

---

**Status**: ✅ All systems operational
**Server**: Running on http://127.0.0.1:8000
**OpenAPI Docs**: http://127.0.0.1:8000/docs
