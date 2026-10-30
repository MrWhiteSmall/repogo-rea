@echo off
cd /d "%~dp0"
py -3 run.py run
if errorlevel 1 goto failed
py -3 run.py serve
exit /b %errorlevel%
:failed
echo Analysis failed. Review the error above.
pause
exit /b 1
