@ECHO OFF
REM Обёртка Wazuh Active Response -> PowerShell. Кладётся в active-response\bin\ на win10.
PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0disable-user.ps1"
EXIT /B %ERRORLEVEL%
