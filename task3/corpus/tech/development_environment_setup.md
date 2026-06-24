# Development Environment Setup

## Document ID: TECH-002
## Min Role: intern

Last Updated: 2025-05-15

## 1. Supported Operating Systems

- macOS 13+ (Ventura or later)
- Ubuntu 22.04 LTS or 24.04 LTS
- Windows 11 with WSL2 (Ubuntu 22.04)

## 2. Required Tools

### Core Tools
- Git 2.40+
- Docker Desktop 4.20+
- Python 3.11+ (via pyenv recommended)
- Node.js 20 LTS (via nvm)
- Go 1.21+

### CLI Tools
- `kubectl` — Follow official Kubernetes install guide
- `helm` v3.12+ — `brew install helm` or `choco install kubernetes-helm`
- `azure-cli` — `brew install azure-cli` or `winget install Microsoft.AzureCLI`
- `terraform` 1.6+ — `brew install terraform`

### IDE
- VS Code (recommended) with extensions: Python, Go, Kubernetes, Docker, Prettier
- IntelliJ IDEA Ultimate for Java/Kotlin projects (license provided)

## 3. Repository Access

- GitHub Enterprise: https://github.acmecorp.com
- Authenticate via SAML SSO (Okta)
- Clone repos via SSH: `git clone git@github.acmecorp.com:team/repo.git`

## 4. Local Services

Use Docker Compose for local development:
```bash
docker compose -f dev/docker-compose.yml up -d
```
This starts PostgreSQL 15, Redis 7, and LocalStack (AWS emulator).

## 5. Environment Variables

Copy `.env.example` to `.env` and fill in required values. Never commit `.env` files.
Use `direnv` or `dotenv` for automatic loading.
