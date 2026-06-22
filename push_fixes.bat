@echo off
cd /d "%~dp0"
echo.
echo =========================================================
echo  PUSHING MOBILE SPEECH AND DIALOGUE FIXES TO GITHUB
echo =========================================================
echo.
git add .
git commit -m "Fix voice recognition, add Hindi/English language toggle, and bind live mic transcription to chat bubbles"
git push origin main
echo.
echo =========================================================
echo  Push complete! Vercel will auto-redeploy.
echo =========================================================
echo.
