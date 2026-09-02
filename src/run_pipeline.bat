@echo off
setlocal

cd /d "C:\Users\HP\OneDrive\Desktop\linkedin-agent-analytics\src"

if not exist "..\logs" mkdir "..\logs"

set LOGFILE=..\logs\pipeline.log

echo ========================================== >> "%LOGFILE%"
echo LinkedIn Agent Analytics Pipeline >> "%LOGFILE%"
echo Started: %date% %time% >> "%LOGFILE%"
echo ========================================== >> "%LOGFILE%"

echo ==========================================
echo LinkedIn Agent Analytics Pipeline
echo Started: %date% %time%
echo ==========================================

python ingest.py >> "%LOGFILE%" 2>&1

set PIPELINE_EXIT_CODE=%ERRORLEVEL%

echo. >> "%LOGFILE%"

IF %PIPELINE_EXIT_CODE% EQU 0 (

    echo PIPELINE SUCCESS: %date% %time% >> "%LOGFILE%"

    echo ==========================================
    echo PIPELINE SUCCESS
    echo Completed: %date% %time%
    echo ==========================================

) ELSE (

    echo PIPELINE FAILED: %date% %time% >> "%LOGFILE%"

    echo ==========================================
    echo PIPELINE FAILED
    echo Completed: %date% %time%
    echo ==========================================

)

exit /b %PIPELINE_EXIT_CODE%