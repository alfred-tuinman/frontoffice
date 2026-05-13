@echo off
:: ─────────────────────────────────────────────────────────────────
::  Booking Converter — Windows Server Startup
::  Edit the variables below to match your environment.
:: ─────────────────────────────────────────────────────────────────

:: MSSQL connection
:: Use Windows Authentication (leave DB_USER blank) or SQL Server auth
SET DB_SERVER=YOUR_SERVER\SQLEXPRESS
SET DB_NAME=YourDatabaseName
SET DB_DRIVER=ODBC Driver 17 for SQL Server
SET DB_USER=
SET DB_PASS=

:: Flask
SET SECRET_KEY=change-me-to-a-long-random-string
SET PORT=5000

echo.
echo  Booking Converter
echo  -----------------
echo  Server : %DB_SERVER%
echo  DB     : %DB_NAME%
echo  Port   : %PORT%
echo.
echo  Open http://localhost:%PORT% in your browser.
echo  Press Ctrl+C to stop.
echo.

cd /d "%~dp0"
waitress-serve --host=0.0.0.0 --port=%PORT% app:app

pause
