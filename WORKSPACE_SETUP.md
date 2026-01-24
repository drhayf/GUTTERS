# GUTTERS Workspace Auto-Activation Setup

## What I've Set Up For You

Your workspace is now configured to **automatically activate the venv** whenever you work here. This means you (and AI agents) won't need to manually activate it!

## VS Code Configuration (Primary Solution)

### Files Created in [.vscode/](.vscode/):

1. **[settings.json](.vscode/settings.json)** - Workspace settings that:
   - Force Python interpreter to use `.venv/Scripts/python.exe`
   - Auto-activate venv in all new terminals
   - Set up PATH to include `.venv/Scripts`
   - Configure Python testing, linting, and formatting

2. **[launch.json](.vscode/launch.json)** - Debug configurations for:
   - FastAPI development server
   - Current file execution
   - Pytest test runner

3. **[extensions.json](.vscode/extensions.json)** - Recommended VS Code extensions

### How It Works:

**When you open a terminal in VS Code:**
- The venv is automatically activated
- You'll see `(gutters)` in your prompt
- All commands (alembic, python, pip) will use the venv
- Agents working in this workspace will also use the activated venv

## Other Auto-Activation Methods

### Option 1: Git Bash Auto-Activation (Advanced)

Add this to your `~/.bashrc`:
```bash
# Source GUTTERS auto-activation if in the project
if [[ -f "/c/dev/GUTTERS/.auto-activate.sh" ]]; then
    source "/c/dev/GUTTERS/.auto-activate.sh"
fi
```

Then the venv will auto-activate whenever you `cd` into the GUTTERS directory!

### Option 2: direnv (If You Have It Installed)

If you use [direnv](https://direnv.net/), run:
```bash
cd /c/dev/GUTTERS
direnv allow
```

The [.envrc](.envrc) file is already configured.

## Verifying It Works

### Test in VS Code:
1. Open a new terminal in VS Code (Ctrl+`)
2. You should see `(gutters)` in the prompt
3. Run: `which python` → Should show: `/c/dev/GUTTERS/.venv/Scripts/python`
4. Run: `pip list` → Should show all 133 packages

### Test Commands (Should All Work Now):
```bash
# No activation needed in VS Code terminals!
alembic revision --autogenerate -m "My changes"
python src/app/main.py
pytest tests/
```

## For AI Agents

When agents work in this VS Code workspace, they will:
- Automatically use the activated venv
- Have access to all installed packages
- Be able to run alembic, pytest, and other commands directly
- Not need to use `.venv/Scripts/python.exe` paths

## Troubleshooting

### If venv isn't auto-activating in VS Code:
1. Reload VS Code window (Ctrl+Shift+P → "Reload Window")
2. Check Python interpreter (bottom right status bar) shows `.venv`
3. Close all terminals and open a new one

### If you see "gutters" but commands still don't work:
- Check that packages are in `.venv`: `source .venv/Scripts/activate && pip list`
- VS Code might be using system Python - select interpreter manually

### To manually activate (if needed):
```bash
source activate.sh  # Git Bash
activate.bat        # CMD/PowerShell
```

## File Summary

### Configuration Files:
- [.vscode/settings.json](.vscode/settings.json) - VS Code workspace settings ⭐ Main solution
- [.vscode/launch.json](.vscode/launch.json) - Debug configurations
- [.vscode/extensions.json](.vscode/extensions.json) - Recommended extensions
- [.envrc](.envrc) - direnv configuration (optional)
- [.auto-activate.sh](.auto-activate.sh) - Bash auto-activation hook (optional)

### Quick Start Scripts:
- [activate.bat](activate.bat) - Manual activation for Windows CMD/PowerShell
- [activate.sh](activate.sh) - Manual activation for Git Bash
- [VENV_SETUP.md](VENV_SETUP.md) - Virtual environment documentation

## The Bottom Line

**In VS Code:** Just open a terminal. The venv is already activated. Done. ✓

**Outside VS Code:** Use `source activate.sh` or set up the Bash hook.

**For Agents:** They'll automatically use the activated venv when working in VS Code.
