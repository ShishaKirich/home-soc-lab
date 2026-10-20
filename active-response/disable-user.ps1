# Active Response: отключение учётной записи, добавленной в администраторы (правило 100141).
# Вызывается Wazuh-агентом на win10 через disable-user.cmd. JSON алерта приходит в stdin.
# Для стенда. Отключает (не удаляет) локальную учётку, чтобы инцидент можно было разобрать.

$ErrorActionPreference = "Stop"
$log = "C:\Program Files (x86)\ossec-agent\active-response\active-responses.log"

function Write-ARLog($msg) {
    $ts = (Get-Date).ToUniversalTime().ToString("yyyy/MM/dd HH:mm:ss")
    Add-Content -Path $log -Value "$ts disable-user: $msg" -Encoding UTF8
}

try {
    $raw = [Console]::In.ReadToEnd()
    $alert = $raw | ConvertFrom-Json

    # command = add (Wazuh просит выполнить реагирование)
    if ($alert.command -ne "add") {
        Write-ARLog "command=$($alert.command), действие не требуется"
        exit 0
    }

    $cmdline = $alert.parameters.alert.data.win.eventdata.commandLine
    # Достаём имя пользователя из "net localgroup administrators <user> /add"
    $user = $null
    if ($cmdline -match '(?i)localgroup\s+\S+\s+"?([^"\s/]+)"?\s+/add') {
        $user = $matches[1]
    }
    if (-not $user) {
        Write-ARLog "не удалось извлечь имя пользователя из: $cmdline"
        exit 1
    }

    $acct = Get-LocalUser -Name $user -ErrorAction SilentlyContinue
    if (-not $acct) {
        Write-ARLog "учётная запись '$user' не найдена"
        exit 1
    }

    Disable-LocalUser -Name $user
    Write-ARLog "учётная запись '$user' ОТКЛЮЧЕНА по правилу $($alert.parameters.alert.rule.id)"
    exit 0
}
catch {
    Write-ARLog "ошибка: $_"
    exit 1
}
