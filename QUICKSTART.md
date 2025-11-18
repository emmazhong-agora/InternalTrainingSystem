# Quick Start Guide

Get the Internal Training System up and running in 15 minutes!

## Prerequisites Check

Make sure you have:
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 14+
- ✅ AWS Account (S3 access)

## Step 1: Database (2 minutes)

```bash
# Create database
psql -U postgres -c "CREATE DATABASE training_system;"
```

## Step 2: Backend (5 minutes)

```bash
# Navigate to backend
cd InternalTrainingSystem-Fresh/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL and AWS credentials

# Run migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend running at: **http://localhost:8000**

## Step 3: Frontend (5 minutes)

```bash
# Open new terminal
cd InternalTrainingSystem-Fresh/frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start dev server
npm run dev
```

Frontend running at: **http://localhost:5173**

## Step 4: Create Admin User (2 minutes)

```bash
# Using curl
curl -X POST "http://localhost:8000/api/v1/auth/admin/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "admin123456",
    "full_name": "Admin User"
  }'
```

Or visit: **http://localhost:5173/register**

## Step 5: Login & Test (1 minute)

1. Visit: **http://localhost:5173/login**
2. Login with your credentials
3. Upload a test video!

## Sample VTT File

Create `test.vtt` for your first video:

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
Welcome to the training system.

00:00:05.000 --> 00:00:10.000
This is a test subtitle.
```

## Minimum .env Configuration

### Backend .env
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/training_system
SECRET_KEY=generate-with-python-secrets-token-urlsafe
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
```

### Frontend .env
```env
VITE_API_URL=http://localhost:8000
```

## Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Common Issues

### "Connection refused" error
- ✅ Check if PostgreSQL is running: `pg_isready`
- ✅ Check if backend is running on port 8000

### "CORS error" in browser
- ✅ Check CORS_ORIGINS in backend .env
- ✅ Restart backend server

### Can't upload video
- ✅ Verify AWS credentials
- ✅ Check S3 bucket exists
- ✅ Ensure IAM user has S3 write permissions

## Next Steps

- 📖 Read `SETUP.md` for detailed instructions
- 🗺️ Check `ROADMAP.md` for future features
- 📋 Review `PRD.md` for complete requirements
- 🚀 Start implementing Phase 2 (AI features)

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Default URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Database | localhost:5432 |

## Success!

You're now ready to use the Internal Training System!

👤 **Login** → 📹 **Browse Videos** → 📤 **Upload (Admin)** → 📊 **Track Progress**

For help, see `SETUP.md` or check the troubleshooting section.
