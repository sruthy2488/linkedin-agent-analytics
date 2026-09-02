@echo off
setlocal

cd /d "C:\Users\HP\OneDrive\Desktop\linkedin-agent-analytics\src"

if not exist "..\logs" mkdir "..\logs"

echo ==========================================
echo LinkedIn Agent Analytics Pipeline
echo Started: %date% %time%
echo ==========================================

python ingest.py

set PIPELINE_EXIT_CODE=%ERRORLEVEL%

IF %PIPELINE_EXIT_CODE% EQU 0 (
    echo ==========================================
    echo PIPELINE SUCCESS
    echo Completed: %date% %time%
    echo ==========================================
) ELSE (
    echo ==========================================
    echo PIPELINE FAILED
    echo Completed: %date% %time%
    echo ==========================================
)

exit /b %PIPELINE_EXIT_CODE%