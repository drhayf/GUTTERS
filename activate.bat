@echo off
REM Quick venv activation script for Windows CMD/PowerShell
echo Activating GUTTERS virtual environment...
call .venv\Scripts\activate.bat
echo.
echo Virtual environment activated!
echo Python: %VIRTUAL_ENV%\Scripts\python.exe
echo.
echo To deactivate, type: deactivate
