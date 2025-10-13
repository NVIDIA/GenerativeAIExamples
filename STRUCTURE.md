# Repository Structure

This document describes the organization of the AI vWS Sizing Advisor repository.

## Root Directory

```
ai-vws-sizing-tool/
├── README.md                 # Main documentation
├── LICENSE                   # Apache 2.0 license
├── LICENSE-3rd-party.txt     # Third-party licenses
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── SECURITY.md               # Security policies
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── .dockerignore             # Docker ignore rules
└── STRUCTURE.md              # This file
```

## Core Directories

### `/src`
**Backend API and core logic**

- `server.py` - FastAPI server
- `chains.py` - RAG chain implementations
- `apply_configuration.py` - vGPU configuration and vLLM deployment
- `calculator.py` - vGPU sizing calculations
- `configuration_wizard.py` - Configuration recommendation engine
- Other utility modules

### `/frontend`
**Next.js web application**

```
frontend/
├── src/
│   ├── app/                  # Next.js app router
│   │   ├── components/       # React components
│   │   ├── page.tsx          # Main page
│   │   └── layout.tsx        # App layout
│   └── types/                # TypeScript types
├── public/                   # Static assets
├── package.json              # npm dependencies
└── README.md                 # Frontend documentation
```

### `/scripts`
**Deployment and utility scripts**

- `start_vgpu_rag.sh` - Start all services
- `stop_vgpu_rag.sh` - Stop all services
- `restart_backend.sh` - Restart backend container

### `/deploy`
**Deployment configurations**

```
deploy/
├── compose/                  # Docker Compose files
│   ├── docker-compose-rag-server.yaml
│   ├── docker-compose-bootstrap.yaml
│   ├── .env                  # Environment variables
│   └── *.yaml                # Other compose files
├── config/                   # Service configurations
│   ├── otel-collector-config.yaml
│   └── prometheus.yaml
└── helm/                     # Kubernetes Helm charts
    └── rag-server/
```

### `/docs`
**Documentation**

- `quickstart.md` - Quick start guide
- `api_reference/` - API specifications
- `VGPU_SIMPLIFIED_SETUP.md` - vGPU setup guide
- `troubleshooting.md` - Common issues
- Various feature guides

### `/data`
**Sample data and test files**

- `multimodal/` - Sample PDF/DOCX files for testing
- `dataset.zip` - Sample dataset
- `LICENSE.DATA` - Data license

### `/vgpu_docs`
**vGPU knowledge base documents**

Place PDF documentation files here for automatic ingestion into the RAG system.

### `/tools`
**Development tools**

- `demo_model_extractor.py` - Interactive model name extractor demo
- `README.md` - Tools documentation

## Generated/Excluded Directories

These directories are created during runtime and excluded from version control:

- `src/__pycache__/` - Python bytecode
- `frontend/node_modules/` - npm packages
- `frontend/.next/` - Next.js build output
- `deploy/compose/volumes/` - Docker volumes
- `.venv/` - Python virtual environment

## Configuration Files

- `.gitignore` - Files excluded from Git
- `.dockerignore` - Files excluded from Docker builds
- `frontend/.env.example` - Frontend environment template
- `deploy/compose/.env` - Docker Compose environment variables

## Key Entry Points

| Purpose | File/Directory |
|---------|---------------|
| **Backend API** | `src/server.py` |
| **Frontend UI** | `frontend/src/app/page.tsx` |
| **Start Services** | `scripts/start_vgpu_rag.sh` |
| **Configuration** | `src/apply_configuration.py` |
| **Deployment** | `deploy/compose/docker-compose-rag-server.yaml` |

## Development Workflow

1. **Backend changes**: Edit files in `/src`
2. **Frontend changes**: Edit files in `/frontend/src`
3. **Deployment configs**: Edit files in `/deploy`
4. **Documentation**: Edit files in `/docs` or root-level `.md` files
5. **Testing**: Use scripts in `/scripts` and tools in `/tools`

## Adding New Features

- **New API endpoint**: Add to `src/server.py`
- **New component**: Add to `frontend/src/app/components/`
- **New documentation**: Add to `/docs`
- **New utility**: Add to `/tools`
- **New sample data**: Add to `/data`

