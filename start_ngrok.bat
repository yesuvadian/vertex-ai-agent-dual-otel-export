@echo off
echo Starting ngrok tunnel...
echo.
echo This will expose localhost:4318 to the internet
echo.
start cmd /k "ngrok http 4318"
echo.
echo ============================================================
echo ngrok is starting in a new window...
echo ============================================================
echo.
echo Wait 5 seconds, then:
echo 1. Look at the ngrok window for the URL (https://xxxxx.ngrok.io)
echo 2. OR visit: http://localhost:4040
echo.
echo Copy the HTTPS URL (not HTTP) and use it to update Cloud Run
echo.
timeout /t 5 /nobreak
start http://localhost:4040
echo.
echo Opening ngrok web interface at http://localhost:4040
echo.
pause
