# Deployment Architecture

# AI Job Agent Version 2

---

## Document Information

| Field | Value |
|-------|-------|
| Document | Deployment Architecture |
| Version | 2.0 |
| Status | Approved |
| Related Documents | System-Architecture.md, Technology-Stack.md, Architecture-Decisions.md |

---

# Purpose

This document defines the production deployment architecture for AI Job Agent Version 2.

It describes:

- Infrastructure topology
- Runtime components
- Deployment environments
- Networking
- Containerization
- Storage
- Security
- Monitoring
- Scalability
- Disaster recovery

This document serves as the infrastructure blueprint for production deployment.

---

# Deployment Goals

The deployment architecture shall provide:

- High reliability
- Horizontal scalability
- Secure communication
- Easy deployments
- Environment isolation
- Automated recovery where practical
- Comprehensive observability
- Production readiness

---

# High-Level Deployment

```text
                    Internet
                        │
                        ▼
                 Reverse Proxy
             (Nginx / Traefik)
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 React Frontend                  FastAPI Backend
 (Static Assets)                (REST API)
                                        │
          ┌─────────────────────────────┼────────────────────────────┐
          ▼                             ▼                            ▼
   PostgreSQL Database         Background Workers             Redis (Optional)
                                        │
                                        ▼
                                 Playwright Workers
                                        │
                                        ▼
                           AI Providers / Job Providers
```

---

# Runtime Components

## Frontend

Responsibilities:

- Serve the user interface
- Handle routing
- Render dashboards
- Submit API requests

Technology:

- React
- TypeScript
- Vite

Deployment:

- Static assets served by a web server or CDN.

---

## Backend API

Responsibilities:

- Authentication
- Business logic
- AI orchestration
- Resume generation
- Job discovery
- Application pipeline

Technology:

- FastAPI
- Uvicorn

Deployment:

- Containerized service

---

## PostgreSQL

Stores:

- Users
- Career profiles
- Resume versions
- Jobs
- Applications
- Scheduler data
- Notifications
- Audit logs

Requirements:

- Persistent storage
- Automated backups
- Regular maintenance
- Point-in-time recovery where supported

---

## Background Workers

Responsibilities:

- AI requests
- Scheduler
- Resume generation
- Browser automation
- Notifications

Workers operate independently of API request handling.

---

## Browser Automation Workers

Responsibilities:

- Launch Playwright
- Navigate job portals
- Complete supported application flows
- Capture diagnostics on failure

Isolation:

Each browser session should execute independently to reduce cross-task interference.

---

# Deployment Environments

## Development

Purpose:

Local development.

Characteristics:

- Local database
- Debug logging
- Development AI providers
- Mock services when appropriate
- Hot reload

---

## Testing

Purpose:

Automated testing.

Characteristics:

- Disposable database
- Automated migrations
- Mock AI providers where appropriate
- Mock job providers where appropriate

---

## Staging

Purpose:

Pre-production validation.

Characteristics:

- Production-like configuration
- Production database schema
- Limited external integrations
- Release candidate testing

---

## Production

Purpose:

End users.

Characteristics:

- High availability
- Monitoring
- Backups
- Secure secrets
- Production logging
- Controlled deployments

---

# Container Architecture

```text
Docker Network
│
├── frontend
├── backend
├── postgres
├── worker
├── playwright
├── redis (optional)
├── nginx
└── monitoring
```

Each service executes independently.

---

# Networking

```text
Internet
    │
    ▼
HTTPS
    │
    ▼
Reverse Proxy
    │
    ▼
Backend API
    │
    ▼
Internal Network
    │
 ┌──┴──────────────┐
 ▼                 ▼
Database       Workers
```

Only the reverse proxy exposes public endpoints.

Internal services communicate over a private network.

---

# Environment Variables

Configuration should include:

```text
DATABASE_URL

JWT_SECRET

OPENROUTER_API_KEY

OLLAMA_HOST

EMAIL_CONFIGURATION

PLAYWRIGHT_CONFIGURATION

LOG_LEVEL

APPLICATION_ENVIRONMENT

CORS_ORIGINS

STORAGE_PATH

SCHEDULER_CONFIGURATION
```

Secrets must never be committed to source control.

---

# Storage

Persistent storage includes:

- Database
- Uploaded resumes
- Generated resumes
- Generated cover letters
- Application attachments
- Logs (based on retention policy)

Temporary files should be cleaned automatically after use.

---

# Security

Production deployment shall include:

- HTTPS
- Secure HTTP headers
- Authentication
- Authorization
- Environment-based secrets
- Input validation
- Rate limiting where appropriate
- Audit logging
- Secure file permissions

---

# Logging

All services should produce structured logs.

Minimum log categories:

- API
- Authentication
- Scheduler
- AI
- Browser automation
- Database
- Errors
- Audit events

Sensitive information should be excluded or appropriately protected.

---

# Monitoring

Operational monitoring should include:

- API health
- Worker health
- Database health
- Scheduler health
- Browser automation health
- AI provider availability
- Job provider availability

---

# Health Checks

Each service should expose a health endpoint where appropriate.

Example:

```text
Frontend
Backend API
Database connectivity
Worker availability
Scheduler availability
```

---

# Backup Strategy

Database:

- Scheduled backups
- Backup verification
- Defined retention policy

Files:

- Resume storage backups
- Attachment backups
- Configuration backups (excluding secrets)

---

# Disaster Recovery

Recovery objectives should be defined for:

- Database restoration
- Resume storage
- Configuration recovery
- Service restart
- Worker restart

Recovery procedures should be documented and periodically tested.

---

# Scalability

The architecture supports:

- Multiple API instances
- Multiple background workers
- Independent Playwright workers
- Independent scheduler workers (with coordination to avoid duplicate execution)
- Database replication (future)
- CDN for static assets
- External object storage (future)

No changes to business logic should be required when increasing infrastructure capacity.

---

# Deployment Workflow

```text
Developer
     │
     ▼
Version Control
     │
     ▼
Continuous Integration
     │
     ▼
Automated Tests
     │
     ▼
Build Container Images
     │
     ▼
Deploy to Staging
     │
     ▼
Validation
     │
     ▼
Deploy to Production
```

---

# Operational Guidelines

Production deployments should:

- Use versioned releases
- Be reversible where practical
- Validate database migrations before release
- Monitor application health after deployment
- Record deployment history

---

# Acceptance Criteria

The deployment architecture is considered complete when:

- All services are independently deployable.
- Configuration is environment-driven.
- Persistent data is protected.
- Internal services are isolated from public access.
- Monitoring and logging are available.
- Backup and recovery procedures are documented.

---

# Related Documents

- System-Architecture.md
- Module-Architecture.md
- Technology-Stack.md
- Architecture-Decisions.md
- Data-Flow.md
- Sequence-Diagrams.md

---

End of Document