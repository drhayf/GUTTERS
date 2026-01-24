# GUTTERS Virtual Environment Setup Guide

## The Problem (What Was Happening)

Your virtual environment (`.venv`) exists and has all packages installed correctly, **BUT it wasn't being activated**. This caused:

1. Commands running against system Python instead of venv Python
2. `pip install` installing packages to `C:\Users\drof\AppData\Roaming\Python\Python312\site-packages` (user site-packages) instead of the venv
3. Commands like `alembic` not being found because they're in `.venv\Scripts\` which wasn't on PATH
4. Confusion about which packages are installed where

## The Solution

### Option 1: Always Activate the venv (RECOMMENDED)

**Before starting work on GUTTERS, activate the virtual environment:**

#### Windows CMD/PowerShell:
```bash
.venv\Scripts\activate
```

#### Git Bash / WSL:
```bash
source .venv/Scripts/activate
```

#### Quick Activation Scripts:
I've created helper scripts for you:
- **activate.bat** - For Windows CMD/PowerShell (just type `activate.bat`)
- **activate.sh** - For Git Bash (just type `source activate.sh`)

When activated, you'll see `(gutters)` at the start of your command prompt.

**To deactivate:**
```bash
deactivate
```

### Option 2: Add venv Scripts to System PATH

If you want to run commands without activating, add this to your system PATH:
```
C:\dev\GUTTERS\.venv\Scripts
```

**How to add to PATH on Windows:**
1. Search for "Environment Variables" in Windows
2. Click "Environment Variables" button
3. Under "User variables", select "Path" and click "Edit"
4. Click "New" and add: `C:\dev\GUTTERS\.venv\Scripts`
5. Click OK on all dialogs
6. Restart your terminal

**Note:** This only works for THIS project's venv. Other projects will need their own venvs.

## How to Install New Packages

**ALWAYS activate the venv first**, then:

```bash
# Activate venv
source .venv/Scripts/activate  # Git Bash
# OR
.venv\Scripts\activate         # CMD/PowerShell

# Add package to pyproject.toml dependencies list, then:
pip install -e .

# Update requirements.txt
pip freeze > requirements.txt
```

## Running Commands

### With Activated venv (Recommended):
```bash
source .venv/Scripts/activate
alembic revision --autogenerate -m "Description"
python -m pytest
uvicorn app.main:app --reload
```

### Without Activation (if Scripts on PATH):
```bash
.venv/Scripts/alembic.exe revision --autogenerate -m "Description"
.venv/Scripts/python.exe -m pytest
```

### Without Activation (using python -m):
```bash
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "Description"
```

## Verification

To check if your venv is activated:
```bash
which python      # Should show: /c/dev/GUTTERS/.venv/Scripts/python
echo $VIRTUAL_ENV # Should show: C:\dev\GUTTERS\.venv (or similar)
```

To check installed packages in venv:
```bash
source .venv/Scripts/activate
pip list
```

## What's Installed

Your venv now has all 133 packages including:
- alembic (database migrations)
- fastapi, uvicorn (web framework)
- sqlalchemy, asyncpg, psycopg (database)
- langchain, openai (LLM/AI)
- pgvector (vector database)
- numpy, scipy, skyfield (astronomy)
- And all their dependencies

## Files Created

- **[activate.bat](activate.bat)** - Windows activation helper
- **[activate.sh](activate.sh)** - Bash activation helper
- **[pyproject.toml](pyproject.toml)** - Source of truth for dependencies (organized & commented)
- **[requirements.txt](requirements.txt)** - Frozen versions for reproducibility (133 packages)

## Best Practice

**Start every work session with:**
```bash
cd c:\dev\GUTTERS
source activate.sh  # or activate.bat on CMD/PowerShell
```

Then all your commands (alembic, python, pip, pytest, etc.) will work correctly!
