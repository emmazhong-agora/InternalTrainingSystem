🚀 AWS Deployment Plan for Internal Training System

  📋 System Overview

  Current Stack:
  - Backend: FastAPI + Python 3.x, PostgreSQL, ChromaDB (vector store), OpenAI, Agora Voice/Video
  - Frontend: React + TypeScript + Vite
  - Storage: AWS S3 (already configured)
  - Features: Video training, AI chat, voice AI, exam management

  ---
  🏗️ Proposed AWS Architecture

  Option 1: Cost-Effective (Recommended for Start)

  ┌─────────────────────────────────────────────────────────────┐
  │                         Users                                │
  └───────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
          ┌───────────────────────────────┐
          │   CloudFront (CDN)            │
          │   - Frontend (React SPA)       │
          └───────────┬───────────────────┘
                      │
          ┌───────────┴──────────┐
          │                      │
          ▼                      ▼
  ┌───────────────┐      ┌──────────────────┐
  │   S3 Bucket   │      │  Application     │
  │   (Static)    │      │  Load Balancer   │
  └───────────────┘      └────────┬─────────┘
                                  │
                      ┌───────────┴──────────┐
                      │                      │
                      ▼                      ▼
              ┌───────────────┐     ┌──────────────┐
              │   ECS Fargate │     │  ECS Fargate │
              │   (Backend 1) │     │  (Backend 2) │
              └───────┬───────┘     └──────┬───────┘
                      │                    │
                      └──────────┬─────────┘
                                 │
                  ┌──────────────┼──────────────┐
                  │              │              │
                  ▼              ▼              ▼
          ┌──────────┐   ┌──────────┐   ┌─────────────┐
          │   RDS    │   │   EFS    │   │  S3 Bucket  │
          │PostgreSQL│   │(ChromaDB)│   │   (Videos)  │
          └──────────┘   └──────────┘   └─────────────┘

  Option 2: Enterprise-Grade (For Production Scale)

  Same as Option 1, but add:
  - ElastiCache Redis for session/cache
  - CloudWatch for monitoring
  - AWS WAF for security
  - Route 53 for DNS
  - AWS Secrets Manager for secrets
  - EC2 Auto Scaling instead of fixed ECS tasks

  ---
  🎯 Recommended AWS Services

  1. Compute & Container

  - AWS ECS Fargate (Backend API)
    - Serverless containers, no EC2 management
    - Auto-scaling based on CPU/memory
    - Cost: ~$30-60/month for 2 tasks (1 vCPU, 2GB RAM each)
  - Alternative: AWS App Runner (Simpler but less control)
    - Fully managed container service
    - Automatic deployments from GitHub
    - Cost: ~$25-50/month

  2. Database

  - Amazon RDS PostgreSQL (db.t3.micro or db.t4g.micro)
    - Managed PostgreSQL with automated backups
    - Multi-AZ for high availability (optional)
    - Cost: ~$15-30/month (single AZ), ~$30-60/month (Multi-AZ)

  3. Storage

  - Amazon S3 (Already configured)
    - Video files storage
    - Static website hosting for frontend
    - Cost: ~$5-20/month depending on storage/transfer
  - Amazon EFS (Elastic File System)
    - For ChromaDB vector store (persistent file storage)
    - Cost: ~$10-30/month (depends on data size)

  4. Content Delivery

  - Amazon CloudFront
    - CDN for frontend assets
    - Reduces latency globally
    - Cost: ~$5-15/month

  5. Load Balancing

  - Application Load Balancer (ALB)
    - Distribute traffic to backend containers
    - HTTPS/SSL termination
    - Cost: ~$16/month + data processing fees

  6. Secrets & Configuration

  - AWS Secrets Manager or Parameter Store
    - Store API keys, database credentials
    - Secrets Manager: $0.40/secret/month
    - Parameter Store: Free for standard parameters

  7. Monitoring & Logs

  - Amazon CloudWatch
    - Application logs
    - Metrics and alarms
    - Cost: ~$5-10/month

  8. Networking

  - VPC (Virtual Private Cloud)
    - Private subnets for database
    - Public subnets for load balancer
    - Cost: Free (NAT Gateway: ~$32/month if needed)

  ---
  💰 Estimated Monthly Costs

  Basic Setup (Development/Small Team)

  | Service                      | Cost       |
  |------------------------------|------------|
  | ECS Fargate (2 tasks)        | $40        |
  | RDS PostgreSQL (db.t3.micro) | $20        |
  | EFS (10GB)                   | $3         |
  | S3 (50GB videos + static)    | $5         |
  | CloudFront                   | $5         |
  | ALB                          | $16        |
  | Secrets Manager              | $2         |
  | CloudWatch                   | $5         |
  | Total                        | ~$96/month |

  Production Setup (50-100 users)

  | Service                                | Cost        |
  |----------------------------------------|-------------|
  | ECS Fargate (3-4 tasks)                | $80         |
  | RDS PostgreSQL (db.t3.small, Multi-AZ) | $60         |
  | EFS (50GB)                             | $15         |
  | S3 (200GB + transfer)                  | $15         |
  | CloudFront                             | $15         |
  | ALB                                    | $20         |
  | NAT Gateway                            | $32         |
  | Secrets Manager                        | $5          |
  | CloudWatch                             | $10         |
  | Total                                  | ~$252/month |

  ---
  📝 Deployment Steps

  Phase 1: Infrastructure Setup

  1.1 VPC & Networking

  # Create VPC with public and private subnets
  - VPC CIDR: 10.0.0.0/16
  - Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (for ALB)
  - Private Subnets: 10.0.10.0/24, 10.0.11.0/24 (for ECS, RDS)
  - Internet Gateway for public subnets
  - NAT Gateway for private subnets (optional)

  1.2 Security Groups

  ALB Security Group:
    - Inbound: 443 (HTTPS) from 0.0.0.0/0
    - Inbound: 80 (HTTP) from 0.0.0.0/0
    - Outbound: All

  ECS Security Group:
    - Inbound: 8000 from ALB Security Group
    - Outbound: All

  RDS Security Group:
    - Inbound: 5432 from ECS Security Group
    - Outbound: None

  EFS Security Group:
    - Inbound: 2049 (NFS) from ECS Security Group
    - Outbound: None

  Phase 2: Database & Storage

  2.1 RDS PostgreSQL

  # Create RDS instance
  - Engine: PostgreSQL 15.x
  - Instance class: db.t3.micro (start small)
  - Storage: 20GB SSD (Auto-scaling enabled)
  - Backup retention: 7 days
  - Enable automated backups
  - Encryption at rest: Enabled
  - Multi-AZ: Optional (for HA)

  2.2 EFS for ChromaDB

  # Create EFS file system
  - Performance mode: General Purpose
  - Throughput mode: Bursting
  - Encryption: Enabled
  - Mount targets in private subnets
  - Access points for backend containers

  2.3 S3 Buckets

  Bucket 1: training-videos-<account-id>
    - Purpose: Video files
    - Versioning: Enabled
    - Lifecycle: Archive old versions to Glacier after 90 days

  Bucket 2: training-frontend-<account-id>
    - Purpose: Frontend static files
    - Static website hosting: Enabled
    - CloudFront origin: Configured

  Phase 3: Backend Deployment

  3.1 Create ECR Repository

  aws ecr create-repository \
    --repository-name internal-training-backend \
    --region us-east-1

  3.2 Build & Push Docker Image

  Create backend/Dockerfile:
  FROM python:3.11-slim

  WORKDIR /app

  # Install system dependencies
  RUN apt-get update && apt-get install -y \
      gcc \
      postgresql-client \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Copy application code
  COPY . .

  # Run database migrations and start server
  CMD alembic upgrade head && \
      uvicorn app.main:app --host 0.0.0.0 --port 8000

  3.3 ECS Task Definition

  {
    "family": "training-backend",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "containerDefinitions": [{
      "name": "backend",
      "image": "<ECR-URI>/internal-training-backend:latest",
      "portMappings": [{
        "containerPort": 8000,
        "protocol": "tcp"
      }],
      "environment": [
        {"name": "API_V1_STR", "value": "/api/v1"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "mountPoints": [{
        "sourceVolume": "chromadb-storage",
        "containerPath": "/app/chroma_db"
      }],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/training-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }],
    "volumes": [{
      "name": "chromadb-storage",
      "efsVolumeConfiguration": {
        "fileSystemId": "<EFS-ID>",
        "transitEncryption": "ENABLED"
      }
    }]
  }

  3.4 ECS Service

  - Launch type: Fargate
  - Desired tasks: 2
  - Load balancer: ALB (target group port 8000)
  - Health check: /api/v1/health
  - Auto-scaling: Target CPU 70%

  Phase 4: Frontend Deployment

  4.1 Build Frontend

  Create frontend/.env.production:
  VITE_API_BASE_URL=https://api.yourtraining.com
  VITE_AGORA_APP_ID=your_agora_app_id

  Create frontend/deploy.sh:
  #!/bin/bash
  # Build frontend
  npm run build

  # Upload to S3
  aws s3 sync dist/ s3://training-frontend-<account-id>/ \
    --delete \
    --cache-control "max-age=31536000" \
    --exclude index.html

  # Upload index.html separately with no cache
  aws s3 cp dist/index.html s3://training-frontend-<account-id>/ \
    --cache-control "no-cache"

  # Invalidate CloudFront cache
  aws cloudfront create-invalidation \
    --distribution-id <DISTRIBUTION-ID> \
    --paths "/*"

  4.2 CloudFront Distribution

  Origin 1: S3 bucket (frontend)
    - Path: /
    - Viewer Protocol: Redirect HTTP to HTTPS

  Origin 2: ALB (backend API)
    - Path: /api/*
    - Viewer Protocol: HTTPS only

  Behaviors:
    - Default: S3 origin
    - /api/*: ALB origin

  Custom domain: training.yourcompany.com
  SSL Certificate: AWS Certificate Manager

  Phase 5: Domain & SSL

  5.1 Route 53

  # Create hosted zone
  - Domain: yourtraining.com

  # A Record (CloudFront alias)
  - Name: training.yourtraining.com
  - Type: A - IPv4 address
  - Alias: Yes
  - Target: CloudFront distribution

  5.2 SSL Certificate

  # Request in ACM (us-east-1 for CloudFront)
  - Domain: *.yourtraining.com
  - Validation: DNS
  - Add CNAME records to Route 53

  Phase 6: Secrets Management

  6.1 Store Secrets

  # Create secrets in AWS Secrets Manager
  aws secretsmanager create-secret \
    --name training/database \
    --secret-string '{"username":"postgres","password":"xxx","host":"xxx.rds.amazonaws.com","port":"5432","database":"training"}'

  aws secretsmanager create-secret \
    --name training/jwt-secret \
    --secret-string "your-secret-key-here"

  aws secretsmanager create-secret \
    --name training/openai \
    --secret-string "sk-xxx"

  # Similar for Agora, AWS keys, etc.

  Phase 7: CI/CD (Optional but Recommended)

  7.1 GitHub Actions Workflow

  Create .github/workflows/deploy.yml:
  name: Deploy to AWS

  on:
    push:
      branches: [main]

  jobs:
    deploy-backend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3

        - name: Configure AWS credentials
          uses: aws-actions/configure-aws-credentials@v2
          with:
            aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
            aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
            aws-region: us-east-1

        - name: Login to ECR
          id: login-ecr
          uses: aws-actions/amazon-ecr-login@v1

        - name: Build and push Docker image
          env:
            ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
            ECR_REPOSITORY: internal-training-backend
            IMAGE_TAG: ${{ github.sha }}
          run: |
            cd backend
            docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
            docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

        - name: Update ECS service
          run: |
            aws ecs update-service \
              --cluster training-cluster \
              --service backend-service \
              --force-new-deployment

    deploy-frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3

        - name: Setup Node
          uses: actions/setup-node@v3
          with:
            node-version: '18'

        - name: Build frontend
          run: |
            cd frontend
            npm ci
            npm run build

        - name: Deploy to S3
          run: |
            cd frontend
            ./deploy.sh

  ---
  🔒 Security Checklist

  - ✅ Use private subnets for backend and database
  - ✅ Enable encryption at rest for RDS and EFS
  - ✅ Enable encryption in transit (HTTPS/TLS)
  - ✅ Store secrets in AWS Secrets Manager
  - ✅ Use IAM roles instead of access keys where possible
  - ✅ Enable CloudTrail for audit logs
  - ✅ Configure AWS WAF rules (optional but recommended)
  - ✅ Enable VPC Flow Logs
  - ✅ Regular security updates for Docker images
  - ✅ Enable MFA for AWS root account

  ---
  📊 Monitoring & Alerting

  CloudWatch Dashboards

  - Backend API response times
  - Database CPU and connections
  - ECS task CPU/memory utilization
  - ALB request counts and error rates
  - S3 storage usage

  CloudWatch Alarms

  - ECS CPU > 80% for 5 minutes
  - RDS CPU > 70% for 5 minutes
  - ALB 5XX errors > 10 per minute
  - RDS Free Storage < 2GB
  - ECS service desired count != running count

  ---
  🚀 Migration Steps

  Step-by-Step Migration

  1. Week 1: Infrastructure Setup
    - Create VPC, subnets, security groups
    - Create RDS PostgreSQL instance
    - Create EFS for ChromaDB
    - Set up S3 buckets
  2. Week 2: Database Migration
    - Export local PostgreSQL database
    - Import to RDS
    - Test connectivity
    - Run Alembic migrations
  3. Week 3: Backend Deployment
    - Create Dockerfile
    - Build and push to ECR
    - Create ECS task definition
    - Deploy ECS service
    - Configure ALB
  4. Week 4: Frontend Deployment
    - Build frontend for production
    - Upload to S3
    - Configure CloudFront
    - Test end-to-end
  5. Week 5: Domain & SSL
    - Configure Route 53
    - Request SSL certificate
    - Update DNS records
  6. Week 6: Testing & Optimization
    - Load testing
    - Performance optimization
    - Set up monitoring
    - Configure auto-scaling

  ---
  📚 Additional Recommendations

  1. Backup Strategy
    - RDS automated backups (7-day retention)
    - Manual snapshots before major changes
    - S3 versioning enabled
    - EFS backups using AWS Backup
  2. Cost Optimization
    - Use Savings Plans for ECS/RDS if long-term
    - Enable S3 Intelligent-Tiering
    - Use Spot instances for non-critical workloads
    - Set up AWS Budgets alerts
  3. Disaster Recovery
    - Multi-AZ RDS for high availability
    - Cross-region S3 replication (optional)
    - Document recovery procedures
    - Regular DR drills

  ---
  Would you like me to:
  1. Create the actual deployment files (Dockerfile, docker-compose, deploy scripts)?
  2. Set up CI/CD pipelines with GitHub Actions?
  3. Create Terraform/CloudFormation templates for infrastructure as code?
  4. Start with a specific phase of the deployment?

  Let me know which approach you prefer, and I'll help you implement it!
