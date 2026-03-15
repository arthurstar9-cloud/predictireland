@echo off
setlocal
cd /d "C:\Users\Joy\predictireland"

if "%~1"=="" (
    echo ERROR: No pillar number specified.
    echo Usage: run_post.bat [1^|2^|3]
    exit /b 1
)

set PILLAR=%~1
set PYTHON=C:\Users\Joy\AppData\Local\Programs\Python\Python312\python.exe
set LOGDIR=%~dp0logs
set TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set LOGFILE=%LOGDIR%\pillar%PILLAR%_%TIMESTAMP%.log

:: Ensure logs directory exists
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo [%date% %time%] Running Pillar %PILLAR%... >> "%LOGFILE%" 2>&1
"%PYTHON%" run.py %PILLAR% >> "%LOGFILE%" 2>&1

if %errorlevel%==0 (
    echo [%date% %time%] Pillar %PILLAR% completed successfully. >> "%LOGFILE%" 2>&1
) else (
    echo [%date% %time%] Pillar %PILLAR% FAILED with exit code %errorlevel%. >> "%LOGFILE%" 2>&1
)
