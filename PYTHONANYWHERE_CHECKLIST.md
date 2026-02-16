# PythonAnywhere Deployment - Quick Checklist

## What You Need to Deploy

### 1. Files to Upload
- ✅ All project files (main.py, database.py, models.py, schemas.py, auth.py)
- ✅ routers/ directory (users.py, settings.py, transactions.py)
- ✅ requirements.txt
- ✅ wsgi_pythonanywhere.py (WSGI configuration)
- ✅ init_pythonanywhere.py (database initialization script)

### 2. Additional Dependencies (for PythonAnywhere)
Add to requirements.txt or install separately:
```bash
pip install a2wsgi
```

### 3. PythonAnywhere Setup Steps

**On PythonAnywhere:**

1. **Upload Code**
   ```bash
   # Option 1: Via Git
   git clone YOUR_REPO_URL attendance
   
   # Option 2: Manual upload via Files tab
   ```

2. **Create Virtual Environment**
   ```bash
   cd ~/attendance/backend
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install a2wsgi  # For WSGI compatibility
   ```

3. **Initialize Database**
   ```bash
   python init_pythonanywhere.py
   ```

4. **Configure Web App**
   - Go to Web tab → Add new web app
   - Choose "Manual configuration"
   - Select Python 3.10
   
5. **Set WSGI File**
   - Open WSGI configuration file
   - Copy content from `wsgi_pythonanywhere.py`
   - Replace `YOUR_USERNAME` with your username
   
6. **Set Virtual Environment**
   - Virtualenv path: `/home/YOUR_USERNAME/attendance/backend/venv`
   
7. **Configure Static Files** (Optional)
   - URL: `/uploads/`
   - Directory: `/home/YOUR_USERNAME/attendance/backend/uploads/`
   
8. **Reload Web App**
   - Click green "Reload" button

9. **Test**
   - Visit: `https://YOUR_USERNAME.pythonanywhere.com/docs`
   - Login with: admin / 123
   - **Change password immediately!**

## Key Differences from Local Development

| Aspect | Local | PythonAnywhere |
|--------|-------|----------------|
| Server | uvicorn (ASGI) | WSGI with a2wsgi adapter |
| URL | http://127.0.0.1:8000 | https://username.pythonanywhere.com |
| Database | ./attendance.db | Same (SQLite) |
| File uploads | ./uploads/ | /home/username/attendance/backend/uploads/ |
| Restart | Auto-reload on changes | Manual reload in Web tab |

## Common Issues & Solutions

### "Module not found"
- Solution: Check virtualenv path in Web tab
- Verify: `pip list` shows all dependencies

### "Database locked"
- Solution: SQLite has limited concurrent write support
- Consider: Upgrading to MySQL (available on PythonAnywhere)

### "502 Bad Gateway"
- Solution: Check error log in Web tab
- Verify: WSGI file syntax is correct
- Ensure: a2wsgi is installed

### Photos not uploading
- Solution: Create uploads directory
  ```bash
  mkdir -p uploads
  chmod 755 uploads
  ```

## PythonAnywhere Account Types

**Free Account:**
- ✅ Good for testing/development
- ⚠️ Limited CPU seconds (100/day)
- ⚠️ No custom domains with HTTPS
- ✅ HTTPS on .pythonanywhere.com

**Paid Account ($5/month+):**
- ✅ More CPU and bandwidth
- ✅ Custom domains
- ✅ Better performance

## After Deployment

- [ ] Test all endpoints at /docs
- [ ] Change admin password
- [ ] Configure settings with real coordinates
- [ ] Create regular users
- [ ] Test photo uploads
- [ ] Set up database backups
- [ ] Monitor error logs

## Your API will be at:
- **Base URL**: `https://YOUR_USERNAME.pythonanywhere.com`
- **OpenAPI Docs**: `https://YOUR_USERNAME.pythonanywhere.com/docs`
- **ReDoc**: `https://YOUR_USERNAME.pythonanywhere.com/redoc`

---

**For detailed instructions, see:** [DEPLOYMENT.md](DEPLOYMENT.md)
