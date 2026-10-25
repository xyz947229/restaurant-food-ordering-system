@echo off
title Restaurant Food Ordering System - DBMS Course Project
echo ===============================================================
echo   Restaurant Food Ordering System (DBMS Project)
echo   Connected to MySQL Database: restaurant_food_ordering
echo ===============================================================
echo.

:: Free port 8000 if any orphaned process is still holding it
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Freeing port 8000 from old process (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo Starting Django Development Server on port 8000...
echo.
echo Access URL: http://127.0.0.1:8000/
echo.

:: Automatically open default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/"

:: Start Django server
python manage.py runserver 0.0.0.0:8000
pause
