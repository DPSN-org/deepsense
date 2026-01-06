# Pull Request Guide

This document outlines two separate pull requests for the DeepSense refactoring.

## PR 1: Framework Refactoring

### Branch Name
```
refactor/framework-core
```

### Description
Refactoring of the DeepSense framework core components, moving from a monolithic structure to a modular framework with clear separation of concerns.

### Changes Included

#### Framework Core (`deepsense/`)
- ✅ Created `deepsense/` package structure
- ✅ Moved `workflow.py` to `deepsense/workflow.py` with dynamic configuration
- ✅ Moved `checkpointer.py` to `deepsense/checkpointer.py` (MongoDB only, decoupled from message history)
- ✅ Moved `datasource.py` to `deepsense/datasource.py` with `@tool` decorator system
- ✅ Moved `summarizer_graph.py` to `deepsense/summarizer_graph.py`
- ✅ Moved `system_prompt.py` from `graph/system_prompt.py` to `deepsense/system_prompt.py`
- ✅ Created `deepsense/utils/` with `token_utils.py` and `s3_utils.py`
- ✅ Created `deepsense/sandbox/` with all sandbox-related files
- ✅ Added `deepsense/__init__.py` with automatic `.env` loading
- ✅ Implemented declarative `@tool` decorator for datasource methods
- ✅ Auto-generation of unified tool descriptions and schemas
- ✅ Removed `chunking_handler` option, made `summarizer_graph` mandatory

#### Files to Include
```
deepsense/
├── __init__.py
├── datasource.py
├── workflow.py
├── checkpointer.py
├── summarizer_graph.py
├── system_prompt.py
├── agents.py
├── sandbox/
│   ├── __init__.py
│   ├── server.py
│   ├── runner.py
│   ├── runner.js
│   ├── Dockerfile.python
│   └── Dockerfile.node
└── utils/
    ├── __init__.py
    ├── token_utils.py
    └── s3_utils.py
```

#### Files Removed
- `config.py` (replaced by automatic `.env` loading)
- All sandbox files from root directory
- `tools/sandbox_tool.py` (moved to framework)

#### Dependencies
- Updated `requirements.txt` (removed redundant packages: psycopg2-binary, asyncpg, jsonschema)

### Git Commands

```bash
# Create and checkout new branch
git checkout -b refactor/framework-core

# Stage framework changes
git add deepsense/
git add requirements.txt

# Remove old files
git rm config.py
git rm sandbox_server.py sandbox_runner.py sandbox_runner.js
git rm Dockerfile.python Dockerfile.node
git rm tools/sandbox_tool.py 2>/dev/null || true

# Commit
git commit -m "refactor: Framework core refactoring

- Created modular deepsense/ package structure
- Moved workflow, checkpointer, datasource to framework
- Implemented @tool decorator system for declarative tool creation
- Added automatic .env file loading
- Moved sandbox to deepsense/sandbox/
- Moved utils to deepsense/utils/
- Made summarizer_graph mandatory for chunking
- Removed redundant dependencies from requirements.txt
- Removed config.py (replaced by auto .env loading)

BREAKING CHANGE: Framework structure reorganized. Import paths changed.
See architecture.md for migration guide."

# Push branch
git push origin refactor/framework-core
```

### PR Title
```
refactor: Framework core modularization and @tool decorator system
```

### PR Body Template
```markdown
## Overview
This PR refactors the DeepSense framework into a modular structure with clear separation between framework core and user implementations.

## Key Changes

### Framework Structure
- Created `deepsense/` package with modular components
- Moved all core components to framework package
- Implemented automatic `.env` file loading

### Tool System
- Added `@tool` decorator for declarative tool creation
- Auto-generation of unified tool descriptions and schemas
- Simplified datasource-to-tool conversion

### Architecture Improvements
- Made `summarizer_graph` mandatory for chunking
- Decoupled checkpointer from message history
- Moved sandbox to framework package

### Dependencies
- Removed redundant packages (psycopg2-binary, asyncpg, jsonschema)
- Cleaned up requirements.txt

## Breaking Changes
- Import paths changed (e.g., `from deepsense import Workflow`)
- `config.py` removed (use `.env` files instead)
- Sandbox files moved to `deepsense/sandbox/`

## Migration Guide
See `architecture.md` for detailed migration instructions.

## Testing
- [ ] Framework imports work correctly
- [ ] Tool creation from datasources works
- [ ] Workflow execution works
- [ ] Checkpointer persists state correctly
```

---

## PR 2: Example Implementation and Documentation

### Branch Name
```
feat/example-implementation-and-docs
```

### Description
Example implementation using the refactored framework, along with comprehensive documentation updates.

### Changes Included

#### Example Implementation (`example/`)
- ✅ Created `example/` folder structure
- ✅ Moved all datasources to `example/datasources/`
- ✅ Updated datasources to use `@tool` decorator
- ✅ Created `example/workflow_instance.py` using framework
- ✅ Created `example/server.py` with FastAPI and message history
- ✅ Created `example/.env.example` with all environment variables
- ✅ Removed `example/tools.py` (replaced by `@tool` decorator)

#### Documentation
- ✅ Created `architecture.md` with comprehensive system architecture
- ✅ Updated `README.md` to focus on framework purpose and getting started
- ✅ Removed detailed utility explanations from README (moved to architecture.md)
- ✅ Added links to architecture.md throughout README
- ✅ Updated README to emphasize analytical insights from datasources

#### Files to Include
```
example/
├── __init__.py
├── workflow_instance.py
├── server.py
├── quick_start.py
├── README.md
├── .env.example
└── datasources/
    ├── __init__.py
    ├── helius_source.py
    ├── jupiter_source.py
    ├── coingecko_source.py
    ├── github_source.py
    ├── weather_source.py
    ├── flight_source.py
    ├── location_source.py
    ├── news_source.py
    ├── dpsn_source.py
    └── crypto_source.py

architecture.md
README.md
```

#### Files Removed
- `example/tools.py` (functionality replaced by `@tool` decorator)

### Git Commands

```bash
# Create and checkout new branch (from main/master after PR1 is merged)
git checkout -b feat/example-implementation-and-docs

# Stage example changes
git add example/
git add architecture.md
git add README.md

# Remove old files
git rm example/tools.py 2>/dev/null || true

# Commit
git commit -m "feat: Example implementation and documentation

- Created example/ folder with complete implementation
- Updated all datasources to use @tool decorator
- Created workflow_instance.py using refactored framework
- Created FastAPI server with message history management
- Added .env.example with all required environment variables
- Created comprehensive architecture.md
- Updated README.md to focus on framework purpose
- Added links to architecture.md throughout documentation

This PR depends on PR #1 (framework refactoring)."

# Push branch
git push origin feat/example-implementation-and-docs
```

### PR Title
```
feat: Example implementation and comprehensive documentation
```

### PR Body Template
```markdown
## Overview
This PR adds a complete example implementation using the refactored framework and comprehensive documentation.

## Key Changes

### Example Implementation
- Complete example in `example/` folder
- All datasources updated to use `@tool` decorator
- Workflow instance using refactored framework
- FastAPI server with message history management
- Environment variable examples

### Documentation
- Comprehensive `architecture.md` with system diagrams
- Updated `README.md` focused on getting started
- Clear separation: README for users, architecture.md for developers

### Documentation Structure
- **README.md**: Getting started guide, framework purpose, quick start
- **architecture.md**: Detailed system architecture, component interactions, design decisions
- **example/README.md**: Example-specific usage instructions

## Dependencies
This PR depends on PR #1 (framework refactoring).

## Testing
- [ ] Example server runs correctly
- [ ] All datasources create tools correctly
- [ ] Workflow processes queries correctly
- [ ] Message history works correctly
- [ ] Documentation links work

## Example Usage
See `example/README.md` for detailed usage instructions.
```

---

## PR Creation Workflow

### Step 1: Create Framework PR
```bash
# On main branch
git checkout main
git pull origin main

# Create framework branch
git checkout -b refactor/framework-core

# Make changes (already done)
# ... commit changes as shown above ...

# Push and create PR
git push origin refactor/framework-core
# Create PR on GitHub/GitLab with title and body from above
```

### Step 2: After Framework PR is Merged
```bash
# Update main
git checkout main
git pull origin main

# Create example/docs branch
git checkout -b feat/example-implementation-and-docs

# Make changes (already done)
# ... commit changes as shown above ...

# Push and create PR
git push origin feat/example-implementation-and-docs
# Create PR on GitHub/GitLab with title and body from above
```

## Checklist

### PR 1 Checklist
- [ ] All framework files in `deepsense/` directory
- [ ] `@tool` decorator implemented and working
- [ ] Automatic `.env` loading works
- [ ] Sandbox moved to `deepsense/sandbox/`
- [ ] Utils moved to `deepsense/utils/`
- [ ] `config.py` removed
- [ ] Redundant dependencies removed from requirements.txt
- [ ] All imports updated
- [ ] Tests pass (if applicable)

### PR 2 Checklist
- [ ] Example folder structure complete
- [ ] All datasources use `@tool` decorator
- [ ] `workflow_instance.py` uses refactored framework
- [ ] `server.py` implements message history
- [ ] `.env.example` includes all variables
- [ ] `architecture.md` created with diagrams
- [ ] `README.md` updated and focused
- [ ] Documentation links work
- [ ] Example server runs correctly

## Notes

1. **PR Order**: Framework PR must be merged first, then Example/Docs PR
2. **Breaking Changes**: Document all breaking changes in PR 1
3. **Migration**: Provide migration guide in architecture.md
4. **Testing**: Ensure both PRs are tested before merging

