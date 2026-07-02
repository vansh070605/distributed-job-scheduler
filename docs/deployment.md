# Production Deployment Guide

This document outlines deployment configurations, load-balancing practices, and cloud-provider setup recommendations for staging and production environments.

## Cloud-Native Deployment Options

### 1. Kubernetes Deployment (Recommended)
- Expose the API pods via an Ingress Controller (e.g., NGINX Ingress) which provides TLS termination and rate-limiting.
- Deploy database migrations as a Kubernetes Job running `alembic upgrade head` before releasing new versions.
- Configure CPU and memory resource requests/limits for Celery Workers and Beat.
- Set up a Horizontal Pod Autoscaler (HPA) to scale Celery Worker pods automatically based on target queue depths (using custom metrics like `prometheus-adapter`).

### 2. AWS ECS / Fargate Deployment
- Package APIs, Workers, and Beat into individual AWS ECS Task Definitions.
- Expose the API Task via an AWS Application Load Balancer (ALB).
- Provision AWS RDS Aurora Postgres with multi-AZ replication to ensure database resilience.
- Provision Amazon ElastiCache for Redis to manage brokers and lock pools.
- Configure ECS Service Auto Scaling metrics based on CPU utilization and queue metrics.

---

## Production Security Checklist
- Disable FastAPI swagger docs (`docs_url=None`) in production.
- Use secure environment secrets (e.g. AWS Secrets Manager or HashiCorp Vault) rather than `.env` files.
- Enforce secure HTTPS/TLS policies for all API calls.
