---
description: Analyze the FastAPI window quotation system codebase
allowed-tools: Read, Bash, Glob, Grep
argument-hint: none
---

# Prime

Understand the FastAPI window quotation system codebase by reading key files and executing analysis commands, then report findings.

## Read

- CLAUDE.md (project instructions and architecture overview)
- tasks.csv (task tracker)
- main.py (core FastAPI application and routes)
- database.py (SQLAlchemy models and database services)
- config.py (application configuration)
- security/ (security implementation modules)
- services/ (business logic services)
- requirements.txt (dependencies)

## Execute

git ls-files | head -20
python -c "import main; print(f'FastAPI app with {len(main.app.routes)} routes')"
find . -name "*.py" -type f | wc -l

## Report

Report your understanding of this FastAPI window quotation system in this format:

**Architecture Summary:**
- Application type and framework
- Key business domain and purpose
- Security implementation status
- Database architecture

**Core Components:**
For each key file/module, report:
`<File/Module Name> - <Purpose and Key Functionality>`

**System Status:**
- Current development phase
- Recent enhancements completed
- Technical debt areas identified