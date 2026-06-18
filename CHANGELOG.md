# Changelog

All notable changes to this project will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [0.3.0] - 2026-06-12

### Added
- `UserProfile` model with `display_name`, `phone`, `timezone`, `notification_email` (OneToOne with User)
- `UserProfileSerializer` with nested update support in `UserSerializer`
- `UserDetailView` replacing `MeView`: GET + PATCH via `RetrieveUpdateAPIView` pattern
- `UserProfile` auto-created on registration via `RegisterSerializer.create()`
- `UserDetailCard` component: full profile edit form with controlled inputs
- Account Settings page with avatar (initials), email and member-since header
- Phone input with country flag and DDI selector (`react-phone-input-2`)
- Timezone selector with search across all world timezones (`react-timezone-select`)
- Inline form validation: required fields, email format, phone minimum length
- Submit guard: blocks request when no fields have changed, shows feedback message
- Save status feedback: `saving` / `success` / `no-changes` states with auto-dismiss
- Avatar in Navbar: circular badge with user initials linking to Profile page
- Active route highlight in Navbar (React Router `NavLink` `.active` class)

### Changed
- CSS reset uncommented — eliminates browser default margin/padding inconsistencies
- `app-content`: `align-items: center` → `align-items: flex-start` (fixes dashboard layout jump on load)
- Navbar: magic numbers replaced with SCSS variables; stale comments removed
- `navbar-brand` font-size uses `$heading-font-size` variable instead of hardcoded `1.5rem`
- Profile styles moved to `styles/components/Profile/` folder (matches `Login/` pattern)
- `dashboard-card--large` replaced with `profile-card` on Profile page (proper separation)

### Fixed
- Dashboard resize/jump when data loads (caused by vertical flex centering)
- Phone input left padding to correctly accommodate flag button
- Timezone dropdown no longer resizes card (portaled to `document.body`)
- `UserSerializer.update()` uses `get_or_create` for `UserProfile` (prevents crash on first edit)

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
- `Dockerfile.local` frontend: `node:16` → `node:20-alpine`

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
