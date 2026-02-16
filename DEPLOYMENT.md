# PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere account (free or paid)
- Git repository with your code (GitHub, GitLab, etc.)

## Step-by-Step Deployment

### 1. Upload Your Code

**Option A: Using Git (Recommended)**
```bash
# In PythonAnywhere Bash console
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git attendance
cd attendance/backend
```

**Option B: Manual Upload**
- Use PythonAnywhere's "Files" tab
- Upload all project files to `/home/YOUR_USERNAME/attendance/backend/`

### 2. Create Virtual Environment

```bash
# In PythonAnywhere Bash console
cd ~/attendance/backend
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Initialize Database

```bash
# Still in the virtual environment
python -c "from database import create_tables; create_tables()"
```

### 4. Configure Web App

**On PythonAnywhere Dashboard:**

1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.10** (or your preferred version)

**Configure ASGI:**

⚠️ **Important**: PythonAnywhere uses WSGI by default. For FastAPI (ASGI), you need a workaround:

**Option A: Use ASGI with uvicorn (Recommended for paid accounts)**
- In Web tab → WSGI configuration file, replace content with:

```python
import sys
import os

# Add your project directory
path = '/home/YOUR_USERNAME/attendance/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Activate virtual environment
activate_this = '/home/YOUR_USERNAME/attendance/backend/venv/bin/activate_this.py'
exec(open(activate_this).read(), {'__file__': activate_this})

# For FastAPI with uvicorn
from main import app
import uvicorn

# PythonAnywhere expects 'application'
application = app
```

**Option B: Convert to WSGI using a2wsgi (For free accounts)**
Add to requirements.txt:
```
a2wsgi==1.7.0
```

Then in WSGI file:
```python
import sys
import os

path = '/home/YOUR_USERNAME/attendance/backend'
if path not in sys.path:
    sys.path.insert(0, path)

from main import app
from a2wsgi import ASGIMiddleware

# Convert ASGI to WSGI
application = ASGIMiddleware(app)
```

### 5. Set Virtual Environment Path

In Web tab:
- **Virtualenv** section: `/home/YOUR_USERNAME/attendance/backend/venv`

### 6. Configure Static Files (Optional)

If serving uploaded photos directly:
- **URL**: `/uploads/`
- **Directory**: `/home/YOUR_USERNAME/attendance/backend/uploads/`

### 7. Update File Paths in Code

Edit `asgi.py` or WSGI file:
```python
project_home = '/home/YOUR_USERNAME/attendance/backend'
```

Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

### 8. Reload Web App

- Click the green **Reload** button in Web tab

### 9. Test Your API

Visit: `https://YOUR_USERNAME.pythonanywhere.com/docs`

## Important Configuration Changes

### Update main.py for Production

Add CORS if accessing from web frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variables

Create `.env` file (don't commit to git):
```
DATABASE_URL=sqlite:///./attendance.db
SECRET_KEY=your-secret-key-here
DEBUG=False
```

Add to requirements.txt:
```
python-dotenv==1.0.0
```

Load in main.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Database Backup

```bash
# Backup database
cp attendance.db attendance.db.backup

# Download from PythonAnywhere
# Use Files tab → Download button
```

## Troubleshooting

### Error: Module not found
- Check virtual environment path in Web tab
- Verify all dependencies installed: `pip list`

### Error: Database locked
- SQLite can have issues with concurrent writes
- Consider upgrading to PostgreSQL for production
- Or use PythonAnywhere's MySQL

### Error: 502 Bad Gateway
- Check error logs in Web tab
- Verify WSGI/ASGI file syntax
- Ensure virtual environment activated

### File upload errors
- Check uploads directory exists: `mkdir -p uploads`
- Verify write permissions: `chmod 755 uploads`

## PythonAnywhere Limitations

**Free Account:**
- ⚠️ ASGI support limited - use a2wsgi converter
- ⚠️ CPU seconds limited (100 seconds/day)
- ⚠️ No HTTPS on custom domains
- ✅ HTTPS on pythonanywhere.com subdomain

**Paid Account:**
- ✅ Full ASGI/uvicorn support
- ✅ More CPU and bandwidth
- ✅ Custom domains with HTTPS

## Alternative: Use WSGI Adapter

For better PythonAnywhere compatibility, install a2wsgi:

```bash
pip install a2wsgi
```

Update requirements.txt and WSGI file as shown in Option B above.

## Files Needed for Deployment

✅ All existing project files
✅ `requirements.txt` (already exists)
✅ `asgi.py` or modified WSGI file
✅ `.env` for environment variables (optional)
✅ This deployment guide

## Quick Checklist

- [ ] Code uploaded to PythonAnywhere
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database initialized
- [ ] Web app configured (WSGI file)
- [ ] Virtual environment path set
- [ ] Static files configured (uploads)
- [ ] Web app reloaded
- [ ] API tested at /docs endpoint
- [ ] Admin password changed from default

## Post-Deployment

1. **Change default admin password** immediately
2. **Configure settings** with actual location coordinates
3. **Test all endpoints** using /docs interface
4. **Set up database backups**
5. **Monitor error logs** regularly

Your API will be available at:
- **API**: `https://YOUR_USERNAME.pythonanywhere.com`
- **Docs**: `https://YOUR_USERNAME.pythonanywhere.com/docs`
