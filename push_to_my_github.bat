@echo off
cd /d "%~dp0"
echo.
echo =========================================================
echo  CLEANING AND PUSHING LIGHTWEIGHT REPOSITORY TO GITHUB
echo =========================================================
echo.
echo Your repository is currently too large (187MB+) because git is 
echo tracking virtual environments (venv), node_modules, and build targets.
echo.

set /p repo_url="Enter your personal GitHub Repository URL: "

if "%repo_url%"=="" (
    echo.
    echo [ERROR] No repository URL was entered. Exiting...
    echo.
    pause
    exit /b
)

echo.
echo Removing old remote configurations...
git remote remove origin >nul 2>&1
git remote add origin %repo_url%

echo.
echo Creating a standard .gitignore file...
(
echo backend/venv/
echo node_modules/
echo target/
echo __pycache__/
echo .idea/
echo .vscode/
echo *.pyc
echo *.db
echo *.log
echo *.apk
) > .gitignore

echo.
echo Untracking heavy files from git memory (index)...
git rm -r --cached backend/venv >nul 2>&1
git rm -r --cached spring-boot-backend/target >nul 2>&1
git rm -r --cached mobile-app/node_modules >nul 2>&1
git rm -r --cached android-app/node_modules >nul 2>&1
git rm -r --cached .idea >nul 2>&1
git rm -r --cached __pycache__ >nul 2>&1
git rm -r --cached backend/__pycache__ >nul 2>&1
git rm -r --cached phase1-prototype/__pycache__ >nul 2>&1

echo.
echo Staging and committing changes...
git add .
git commit -m "Clean repository: untrack dependencies and add .gitignore"

echo.
echo Pushing lightweight code to GitHub...
git branch -M main
git push -u origin main --force

echo.
echo =========================================================
echo  Code successfully cleaned and pushed to your GitHub!
echo =========================================================
echo.
pause
