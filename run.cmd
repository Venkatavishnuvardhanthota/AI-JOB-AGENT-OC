@echo off
py -3 "%~dp0scripts\launcher.py" start %*
exit /b %ERRORLEVEL%
