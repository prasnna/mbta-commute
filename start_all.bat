@echo off
echo Starting all MBTA commute services...

:: Start each service in its own window
start "Red Line Monitor" cmd /c "cd /d %~dp0\src && Red_Line_Script.bat"
start "Bus 226 Monitor" cmd /c "cd /d %~dp0\src && 226_Bus_Script.bat"
start "Commute Bridge" cmd /c "cd /d %~dp0\src && Commute_Bridge_Script.bat"

echo All services started. Check individual windows for output.
