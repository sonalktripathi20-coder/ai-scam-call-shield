@echo off

echo ==============================================
echo Locating Java (JDK) on your system...
echo ==============================================

rem Check if JAVA_HOME is already defined and valid with jlink
if defined JAVA_HOME (
    if exist "%JAVA_HOME%\bin\java.exe" if exist "%JAVA_HOME%\bin\jlink.exe" (
        echo Found Java at JAVA_HOME: "%JAVA_HOME%"
        goto run_build
    )
)

rem Search common Android Studio JDK/JBR paths on Windows
set "FOUND_JAVA="
for %%p in (
    "C:\Program Files\Android\Android Studio\jbr"
    "C:\Program Files\Android\Android Studio\jre"
    "%LOCALAPPDATA%\Android\android-studio\jbr"
    "%LOCALAPPDATA%\Android\android-studio\jre"
    "%LOCALAPPDATA%\Android\Android Studio\jbr"
    "%LOCALAPPDATA%\Android\Android Studio\jre"
    "C:\Program Files (x86)\Android\Android Studio\jre"
) do (
    if exist "%%~p\bin\java.exe" if exist "%%~p\bin\jlink.exe" (
        set "FOUND_JAVA=%%~p"
        goto found
    )
)

rem Search for JetBrains JBR (IntelliJ IDEA)
for /d %%d in ("C:\Program Files\JetBrains\IntelliJ IDEA *") do (
    if exist "%%d\jbr\bin\java.exe" if exist "%%d\jbr\bin\jlink.exe" (
        set "FOUND_JAVA=%%d\jbr"
        goto found
    )
)

rem Search for Eclipse Adoptium JDKs
for /d %%d in ("C:\Program Files\Eclipse Adoptium\jdk-*") do (
    if exist "%%d\bin\java.exe" if exist "%%d\bin\jlink.exe" (
        set "FOUND_JAVA=%%d"
        goto found
    )
)

rem Search for Oracle or OpenJDK
for /d %%d in ("C:\Program Files\Java\jdk-*") do (
    if exist "%%d\bin\java.exe" if exist "%%d\bin\jlink.exe" (
        set "FOUND_JAVA=%%d"
        goto found
    )
)

:found
if "%FOUND_JAVA%"=="" (
    echo [WARNING] Could not find any Java JDK installation containing jlink automatically.
    echo Please input the path to your Java installation folder containing bin\jlink.exe, for example C:\Program Files\Java\jdk-24 :
    set /p "FOUND_JAVA=Path: "
)

if not exist "%FOUND_JAVA%\bin\java.exe" (
    echo [ERROR] Invalid Java path. Please install a JDK or configure Android Studio.
    pause
    exit /b 1
)

echo Temporarily setting JAVA_HOME to: "%FOUND_JAVA%"
set "JAVA_HOME=%FOUND_JAVA%"
set "PATH=%JAVA_HOME%\bin;%PATH%"

:run_build
echo.
echo ==============================================
echo Building React Native Expo App (mobile-app)...
echo ==============================================
cd mobile-app
echo Installing NPM dependencies...
call npm install --legacy-peer-deps
echo.
echo Running Expo Prebuild to generate android folder...
call npx expo prebuild --platform android
echo.
if not exist android (
    echo [ERROR] expo prebuild failed to create the native android project folder.
    pause
    exit /b 1
)

echo Compiling Android APK via Gradle...
cd android
call gradlew.bat assembleRelease
echo.
echo ==============================================
echo BUILD RESULT:
echo If successful, your APK is located at:
echo mobile-app\android\app\build\outputs\apk\release\app-release.apk
echo ==============================================
pause
