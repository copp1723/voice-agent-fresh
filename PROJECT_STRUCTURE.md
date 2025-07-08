# Project Structure

This document describes the organized structure of the Voice Agent project after cleanup.

## Directory Structure

```
voice-agent-fresh-main/
├── README.md                    # Main project documentation
├── PROJECT_STRUCTURE.md         # This file
├── requirements.txt             # Python dependencies
├── requirements-core.txt        # Core Python dependencies
├── requirements-ml.txt          # ML-specific dependencies
├── requirements-py313.txt       # Python 3.13 specific dependencies
│
├── src/                         # Main application source code
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── database/                # Database related modules
│   ├── middleware/              # Middleware components
│   ├── models/                  # Data models
│   ├── routes/                  # API routes
│   ├── services/                # Business logic services
│   ├── static/                  # Static assets
│   └── utils/                   # Utility functions
│
├── frontend/                    # React frontend application
│   ├── src/                     # Frontend source code
│   ├── public/                  # Public assets
│   ├── package.json             # Node dependencies
│   └── vite.config.ts          # Vite configuration
│
├── chatterbox/                  # Chatterbox TTS/VC integration
│   ├── src/                     # Chatterbox source
│   └── pyproject.toml          # Chatterbox package config
│
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest configuration
│   └── test_*.py               # Test files
│
├── scripts/                     # Utility scripts
│   ├── setup_project.py        # Project setup script
│   ├── start_*.py              # Various startup scripts
│   ├── test_*.py               # Test scripts
│   ├── create_*.py             # Creation utilities
│   └── migrate_*.py            # Migration scripts
│
├── docs/                        # Documentation
│   ├── DEPLOYMENT_GUIDE.md     # Deployment instructions
│   ├── QUICK_START_GUIDE.md    # Quick start guide
│   ├── UI_IMPLEMENTATION_GUIDE.md
│   └── [other documentation files]
│
├── config/                      # Configuration files
│   ├── *.json                  # JSON config files
│   ├── *.yaml                  # YAML config files
│   └── *.ini                   # INI config files
│
├── docker/                      # Docker configuration
│   ├── Dockerfile              # Main Docker image
│   ├── Dockerfile-py313        # Python 3.13 Docker image
│   ├── docker-compose.yml      # Development compose
│   ├── docker-compose.prod.yml # Production compose
│   └── nginx-prod.conf         # Nginx configuration
│
├── server/                      # Additional server components
│   ├── migrations/             # Database migrations
│   ├── models/                 # Enhanced models
│   ├── routes/                 # Additional routes
│   └── services/               # Additional services
│
├── voice_samples/               # Voice sample files
│   └── *.wav                   # Sample audio files
│
├── instance/                    # Instance-specific files
│   └── app.db                  # SQLite database
│
└── app.db                      # Application database

```

## Key Files and Their Purposes

### Root Directory
- **README.md**: Main project documentation and setup instructions
- **requirements*.txt**: Python dependencies organized by purpose
- **app.db**: SQLite database file

### Scripts Directory
- **setup_project.py**: Initial project setup and configuration
- **start_*.py**: Various startup scripts for different environments
- **test_*.py**: Test and verification scripts
- **create_admin_user.py**: Admin user creation utility
- **migrate_database.py**: Database migration tool

### Docker Directory
- **Dockerfile**: Production Docker image configuration
- **docker-compose.yml**: Development environment setup
- **docker-compose.prod.yml**: Production deployment configuration

### Config Directory
- Contains all configuration files previously scattered in root
- Includes JSON, YAML, and INI configuration files

### Docs Directory
- All markdown documentation files except README.md
- Deployment guides, implementation summaries, and setup instructions

## Running the Application

### Local Development
```bash
python scripts/start_enhanced.py
```

### Docker Development
```bash
cd docker
docker-compose up
```

### Production Deployment
```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

## Important Notes

1. All Python scripts in the `scripts/` directory have been updated to properly handle imports from the `src/` directory.
2. Docker files have been updated to reference files from the parent directory correctly.
3. The main application code remains in `src/` following Python best practices.
4. Test files remain in the `tests/` directory for proper test discovery.
5. Configuration files are centralized in `config/` for easy management.