# Setup Guide - Internal Training System

This guide will help you set up and run the Internal Training System on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download](https://nodejs.org/)
- **PostgreSQL 14 or higher** - [Download](https://www.postgresql.org/download/)
- **AWS Account** - For S3 storage
- **Git** - For version control

## Part 1: Database Setup

### 1.1 Install PostgreSQL

If you haven't already, install PostgreSQL for your operating system.

### 1.2 Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE training_system;

# Create user (optional)
CREATE USER training_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE training_system TO training_admin;

# Exit
\q
```

## Part 2: AWS S3 Setup

### 2.1 Create S3 Bucket

1. Log in to AWS Console
2. Navigate to S3
3. Create a new bucket (e.g., `training-videos-your-company`)
4. Set appropriate permissions (or use IAM user credentials)
5. Note your bucket name and region

### 2.2 Create IAM User

1. Navigate to IAM in AWS Console
2. Create a new user with programmatic access
3. Attach policy: `AmazonS3FullAccess` (or create custom policy)
4. Save the Access Key ID and Secret Access Key

## Part 3: Backend Setup

### 3.1 Navigate to Backend Directory

```bash
cd InternalTrainingSystem-Fresh/backend
```

### 3.2 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 3.4 Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

Update the following in `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/training_system

# Security (generate a strong secret key)
SECRET_KEY=your-very-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_BUCKET_NAME=training-videos-your-company
AWS_REGION=us-east-1

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

**Generate a secure SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.5 Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic revision --autogenerate -m "Initial migration"

# Run migrations
alembic upgrade head
```

### 3.6 Start Backend Server

```bash
uvicorn app.main:app --reload
```

The backend will be running at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## Part 4: Frontend Setup

### 4.1 Navigate to Frontend Directory

Open a new terminal window:

```bash
cd InternalTrainingSystem-Fresh/frontend
```

### 4.2 Install Dependencies

```bash
npm install
```

### 4.3 Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env
```

Update the following in `.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 4.4 Start Frontend Development Server

```bash
npm run dev
```

The frontend will be running at: http://localhost:5173

## Part 5: Initial Admin User Setup

### 5.1 Create Admin User

You have two options:

**Option 1: Via API (Postman/cURL)**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/admin/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "admin123456",
    "full_name": "System Administrator"
  }'
```

**Option 2: Via Frontend**

1. Open http://localhost:5173/register
2. Register normally (you can modify the backend code to make the first user an admin automatically)

## Part 6: Testing the Application

### 6.1 Login

1. Navigate to http://localhost:5173/login
2. Use your admin credentials
3. You should be redirected to the home page

### 6.2 Upload a Test Video

1. Click "Upload" in the navigation
2. Fill in the form:
   - Title: "Test Training Video"
   - Description: "This is a test video"
   - Video File: Any MP4 file
   - Transcript File: Create a simple VTT file (see below)
3. Click "Upload Video"

**Sample VTT File (test.vtt):**

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
This is a test training video.

00:00:05.000 --> 00:00:10.000
It demonstrates the video playback functionality.

00:00:10.000 --> 00:00:15.000
You can add subtitles and transcripts in VTT format.
```

### 6.3 Watch Video

1. Navigate to "Videos" page
2. Click on the uploaded video
3. Video should start playing
4. Progress should be tracked automatically

## Part 7: Troubleshooting

### Common Issues

#### Backend won't start

- **Check PostgreSQL**: Ensure PostgreSQL is running
  ```bash
  # macOS
  brew services list

  # Linux
  sudo systemctl status postgresql
  ```
- **Check DATABASE_URL**: Verify connection string in `.env`
- **Port conflict**: Ensure port 8000 is not in use

#### Frontend won't start

- **Node modules**: Try deleting `node_modules` and running `npm install` again
- **Port conflict**: Ensure port 5173 is not in use
- **Check API connection**: Verify `VITE_API_URL` in `.env`

#### Video upload fails

- **Check S3 credentials**: Verify AWS credentials in backend `.env`
- **Check bucket permissions**: Ensure IAM user has write access
- **File size**: Check if file exceeds size limit (default 500MB)
- **Check CORS**: Ensure S3 bucket has proper CORS configuration

#### Login fails

- **Check credentials**: Verify username/password
- **Check backend**: Ensure backend is running
- **Browser console**: Check for error messages
- **CORS errors**: Verify CORS_ORIGINS in backend `.env`

### Database Reset

If you need to reset the database:

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE training_system;"
psql -U postgres -c "CREATE DATABASE training_system;"

# Run migrations again
cd backend
alembic upgrade head
```

## Part 8: Production Deployment (Future)

For production deployment, consider:

1. **Backend**:
   - Use production WSGI server (Gunicorn + Uvicorn)
   - Set up HTTPS
   - Use environment-specific `.env` files
   - Set DEBUG=False

2. **Frontend**:
   - Build production bundle: `npm run build`
   - Serve with Nginx or similar
   - Set up CDN for static assets

3. **Database**:
   - Use managed PostgreSQL (AWS RDS, etc.)
   - Set up regular backups
   - Enable SSL connections

4. **S3**:
   - Set up CloudFront CDN
   - Enable versioning
   - Configure lifecycle policies

## Next Steps

You now have a fully functional MVP of the Internal Training System!

### Phase 2: AI Enhancement (Coming Soon)

The next phase will add:
- AI-powered content analysis (summaries, outlines)
- Intelligent chat assistant
- Automated assessment generation
- Learning analytics

To prepare for Phase 2:
- Get an OpenAI API key
- Add to backend `.env`: `OPENAI_API_KEY=your-key`

### Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Video.js Documentation](https://videojs.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)

## Support

For issues or questions, check:
1. This documentation
2. The PRD.md file for feature details
3. Backend API docs at http://localhost:8000/docs
