# Установка Sysmon и Wazuh Agent на Windows-ВМ стенда.
# Запускать ВНУТРИ ВМ win10 от имени администратора:
#   powershell -ExecutionPolicy Bypass -File .\install-agent.ps1 -WazuhVersion 4.x.y-1
# Версию агента берите ту же, что у Wazuh Manager (видна в Dashboard → About).

param(
    [Parameter(Mandatory = $true)][string]$WazuhVersion,
    [string]$Manager = "192.168.56.10",
    [string]$AgentName = "win10-lab"
)

$ErrorActionPreference = "Stop"
$work = "C:\soc-lab-install"
New-Item -ItemType Directory -Force $work | Out-Null
Set-Location $work

# --- 1. Sysmon (Microsoft Sysinternals) + конфиг sysmon-modular (Olaf Hartong) ---
Write-Host "[*] Скачиваю Sysmon"
Invoke-WebRequest "https://download.sysinternals.com/files/Sysmon.zip" -OutFile Sysmon.zip
Expand-Archive Sysmon.zip -DestinationPath .\Sysmon -Force

Write-Host "[*] Скачиваю конфиг sysmon-modular"
Invoke-WebRequest "https://raw.githubusercontent.com/olafhartong/sysmon-modular/master/sysmonconfig.xml" -OutFile sysmonconfig.xml

if (Get-Service Sysmon64 -ErrorAction SilentlyContinue) {
    Write-Host "[*] Sysmon уже установлен, обновляю конфиг"
    .\Sysmon\Sysmon64.exe -c sysmonconfig.xml
} else {
    Write-Host "[*] Устанавливаю Sysmon"
    .\Sysmon\Sysmon64.exe -accepteula -i sysmonconfig.xml
}

# --- 2. Wazuh Agent ---
$msi = "wazuh-agent-$WazuhVersion.msi"
Write-Host "[*] Скачиваю $msi"
Invoke-WebRequest "https://packages.wazuh.com/4.x/windows/$msi" -OutFile $msi
Start-Process msiexec.exe -Wait -ArgumentList "/i $msi /q WAZUH_MANAGER=$Manager WAZUH_AGENT_NAME=$AgentName"

# --- 3. Сбор журналов Sysmon, PowerShell и Defender ---
$ossec = "C:\Program Files (x86)\ossec-agent\ossec.conf"
$extra = @"

<ossec_config>
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  <localfile>
    <location>Microsoft-Windows-PowerShell/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
  <localfile>
    <location>Microsoft-Windows-Windows Defender/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>
</ossec_config>
"@
if (-not (Select-String -Path $ossec -Pattern "Sysmon/Operational" -Quiet)) {
    Add-Content -Path $ossec -Value $extra -Encoding UTF8
}

# --- 4. Расширенный аудит Windows ---
Write-Host "[*] Включаю аудит и журналирование PowerShell"
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable | Out-Null
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable | Out-Null
auditpol /set /subcategory:"Logon" /success:enable /failure:enable | Out-Null
auditpol /set /subcategory:"Other Object Access Events" /success:enable /failure:enable | Out-Null  # события планировщика (4698)

$psLog = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
New-Item -Path $psLog -Force | Out-Null
Set-ItemProperty -Path $psLog -Name EnableScriptBlockLogging -Value 1

Restart-Service WazuhSvc
Write-Host "[+] Готово. Проверьте агента: Wazuh Dashboard → Agents (статус Active)."
