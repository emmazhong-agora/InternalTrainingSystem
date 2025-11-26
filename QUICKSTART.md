# Quick Start Guide

Get the Internal Training System up and running in 15 minutes!

## Prerequisites Check

Make sure you have:
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ PostgreSQL 14+
- ✅ AWS Account (S3 access)

## Step 1: Configure Deployment (2 minutes)

```bash
cd InternalTrainingSystem-Fresh
cp deployment/config.example.toml deployment/config.toml
# Edit deployment/config.toml with your database, AWS S3, OpenAI, Agora, Microsoft TTS, and ElevenLabs values

# Generate local env files (optional but handy for direct dev servers)
python3 deployment/render_env.py \
  --config deployment/config.toml \
  --backend-env backend/.env \
  --frontend-env frontend/.env
```

> The same `deployment/config.toml` also powers Docker deployments via `./docker-start.sh`.

## Step 2: Database (2 minutes)

```bash
# Create database
psql -U postgres -c "CREATE DATABASE training_system;"
```

## Step 3: Backend (5 minutes)

```bash
# From project root, refresh backend env if config changed
python3 deployment/render_env.py --config deployment/config.toml --backend-env backend/.env

# Navigate to backend
cd InternalTrainingSystem-Fresh/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

Backend running at: **http://localhost:8000**

## Step 4: Frontend (5 minutes)

```bash
# Open new terminal
cd InternalTrainingSystem-Fresh/frontend

# Install dependencies
npm install

# From project root, refresh frontend env if config changed
python3 deployment/render_env.py --config deployment/config.toml --frontend-env frontend/.env

# Start dev server
npm run dev
```

Frontend running at: **http://localhost:5173**

## Step 5: Create Admin User (2 minutes)

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

## Step 6: Login & Test (1 minute)

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

## Minimum `deployment/config.toml` Snippet

```toml
[database]
name = "training_system"
user = "postgres"
password = "yourpassword"
host = "localhost"
port = 5432
driver = "postgresql+psycopg"

[app]
secret_key = "generate-with-python-secrets-token-urlsafe"
cors_origins = ["http://localhost:5173"]

[aws]
access_key_id = "your-aws-key"
secret_access_key = "your-aws-secret"
bucket_name = "your-bucket-name"
region = "us-east-1"

[openai]
api_key = "sk-your-key"

[frontend]
api_base_url = "http://localhost:8000"

[docker]
apt_mirror = ""  # Optional: e.g., "mirrors.aliyun.com" for China-based servers
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
- ✅ Check `cors_origins` inside `deployment/config.toml`
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
