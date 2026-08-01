@echo off
py -3 "%~dp0scripts\launcher.py" status %*
exit /b %ERRORLEVEL%
