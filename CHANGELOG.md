# Changelog

All notable changes to this project will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [Unreleased]

### Planned
- Personal finance dashboard (credit card statement importer)
- JWT authentication (djangorestframework-simplejwt)
- Transaction model with PostgreSQL range partitioning by month
- Materialized views for monthly aggregations
- Parsers for Nubank, Inter and BTG CSV formats
- Auto-categorization by keyword rules
- Charts: spending by category, monthly evolution, top merchants
- BRIN index on transaction date column
- Seed script with synthetic data to demonstrate partition pruning

---

## [0.2.0] - 2026-06-01

### Added
- Makefile with targets for local dev, migrations, tests and ECR deploy
- Vite 5 replacing react-scripts (eliminates CRA peer dependency hell)
- `vite.config.js` with polling watch for Docker bind mounts
- Root `index.html` as Vite entry point
- `sass` (Dart Sass) replacing `node-sass` (no native compilation)
- React Router with pages: Home, Login, Profile, Dashboard
- ThemeContext: dark/light mode with localStorage persistence
- FileContext and Dashboard components (work in progress)
- AuthContext placeholder (not yet connected to backend)

### Changed
- Renamed all `.js` files with JSX syntax to `.jsx`
- `axiosConfig.js`: `process.env` → `import.meta.env` (Vite env API)
- `postgres:16-alpine` pinned in docker-compose (avoids Postgres 18 mount incompatibility)
- `Dockerfile.prod` frontend: build output path `build/` → `dist/`
- `Dockerfile.dev` frontend: `node:16` → `node:20-alpine`

### Fixed
- Docker volume conflict with Postgres 18 breaking local DB startup
- `bash` not available in Alpine containers (changed to `sh` in Makefile)
- `node-sass` compilation failure due to missing build tools in Docker

---

## [0.1.0] - 2026-01-01 (estimated)

### Added
- Terraform infrastructure: VPC, ECS Fargate, 2 ALBs, ECR, CloudWatch
- Remote Terraform backend: S3 + DynamoDB state lock
- Bootstrap pipeline: creates S3/DynamoDB before main infra
- 4 GitHub Actions pipelines: deploy-infra, deploy-hosted-zone, deploy-acm-https, destroy
- Route53 hosted zone + ACM certificates (www + api subdomains)
- Django backend: CSV upload, file listing, health check endpoint
- React frontend: CSV upload form, uploaded files list
- Docker Compose for local development (backend + frontend + postgres)
- Docker Compose for CI tests (no bind mounts)
- Nginx: frontend serves React build + proxies `/api/` to backend ALB
- Nginx: backend proxies to Gunicorn via Unix socket
- Service Discovery for DB container (db-service.db.local)
- 9 documentation files covering infra, CI/CD, routing, HTTPS, local dev, errors learned

### Architecture decisions recorded
- ECS Fargate for DB container (ephemeral by design for dev/cost; RDS for production)
- Two ALBs (frontend + backend) for independent scaling and routing
- `idle_timeout = 300s` on ALBs for large file uploads
- `proxy_request_buffering off` disabled on small instances to avoid OOM
- `envsubst` at container runtime for REACT_APP_BACKEND_URL (not build-time)
