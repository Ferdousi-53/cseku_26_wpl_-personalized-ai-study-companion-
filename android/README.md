# StudyMate AI for Android

This Gradle project packages the existing Flask website in an Android WebView.
The Flask backend continues to run on the laptop; it is not deployed or bundled
into the APK. Keep the phone connected over USB while using the app.

## Build and install on Windows

From the project root, start the website in one PowerShell window:

```powershell
.\venv_new\Scripts\python.exe run.py
```

In a second PowerShell window, build and install the debug APK, then forward the
phone's local port to the Flask server on the laptop:

```powershell
$env:JAVA_HOME = "$env:LOCALAPPDATA\Programs\Microsoft\jdk-17\jdk-17.0.20.1+1"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
.\android\gradlew.bat -p .\android assembleDebug
& "$env:ANDROID_HOME\platform-tools\adb.exe" install -r .\android\app\build\outputs\apk\debug\app-debug.apk
& "$env:ANDROID_HOME\platform-tools\adb.exe" reverse tcp:5000 tcp:5000
```

Open **StudyMate AI** on the phone. If the app was opened before the server or
port forwarding was ready, use **Retry** in the app. The server and USB port
forwarding must remain active while using it. Android file selection is
supported for the website's document uploads.

The APK is created at
`android\app\build\outputs\apk\debug\app-debug.apk`.
