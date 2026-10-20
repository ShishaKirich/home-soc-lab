# Генератор фоновой «обычной» активности для замера ложных срабатываний (пункт 4).
# Запускать ВНУТРИ win10 после отката к снимку baseline-telemetry. Атаки НЕ запускать.
# Цель — наполнить телеметрию легитимными действиями и посмотреть, что из наших правил
# ошибочно сработает. По итогу: scripts/fp_report.py на выгруженных алертах.

param([int]$Minutes = 60)

$end = (Get-Date).AddMinutes($Minutes)
Write-Host "[*] Фоновая активность до $end. Ctrl+C для остановки."

$benign = {
    # Безобидные команды, похожие по форме на разведку — проверяем пороги правил 100170/100171
    whoami | Out-Null
    ipconfig /all | Out-Null
    Get-Process | Out-Null
    # Легитимный PowerShell без -enc
    powershell -Command "Get-Date" | Out-Null
    # Обычная сетевая активность
    try { Invoke-WebRequest "http://192.168.56.10" -UseBasicParsing -TimeoutSec 3 | Out-Null } catch {}
    # Работа с файлами
    $f = "$env:TEMP\bench_$(Get-Random).txt"
    "test" | Out-File $f; Get-Content $f | Out-Null; Remove-Item $f -Force
}

while ((Get-Date) -lt $end) {
    & $benign
    Start-Sleep -Seconds (Get-Random -Minimum 20 -Maximum 90)
}
Write-Host "[+] Готово. Выгрузите alerts.json и запустите fp_report.py."
