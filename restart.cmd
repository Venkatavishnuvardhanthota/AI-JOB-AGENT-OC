@echo off
py -3 "%~dp0scripts\launcher.py" restart %*
exit /b %ERRORLEVEL%
