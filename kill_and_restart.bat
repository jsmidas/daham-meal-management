@echo off
echo Killing process on port 8010...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8010 ^| findstr LISTENING') do (
    echo Killing PID: %%a
    taskkill /F /PID %%a
)
echo Waiting...
ping 127.0.0.1 -n 3 > nul
echo Starting new API server...
start /B python test_samsung_api.py
echo API server started!