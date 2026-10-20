# Настройка сети стенда в VirtualBox (запускать на хосте, все ВМ должны быть выключены).
# Каждой ВМ: nic1 = NAT (интернет для установки пакетов), nic2 = host-only 192.168.56.0/24 (сеть стенда).
# Сетевой мост (bridged) убирается, чтобы стенд не торчал в домашнюю сеть.

param(
    [string[]]$VMs = @("wazuh", "jusyshop", "kali")
)

$ErrorActionPreference = "Stop"
$vbox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$hostOnly = "VirtualBox Host-Only Ethernet Adapter"

$existing = & $vbox list vms | ForEach-Object { ($_ -split '"')[1] }

foreach ($vm in $VMs) {
    if ($existing -notcontains $vm) {
        Write-Warning "ВМ '$vm' не найдена, пропускаю"
        continue
    }
    $state = (& $vbox showvminfo $vm --machinereadable | Select-String '^VMState=').ToString()
    if ($state -notmatch 'poweroff|saved|aborted') {
        Write-Warning "ВМ '$vm' запущена ($state). Выключите её и запустите скрипт снова."
        continue
    }

    Write-Host "[*] $vm : снимок 'before-soc-lab'"
    & $vbox snapshot $vm take "before-soc-lab" --description "Состояние до настройки SOC-стенда" | Out-Null

    Write-Host "[*] $vm : nic1=NAT, nic2=host-only"
    & $vbox modifyvm $vm --nic1 nat
    & $vbox modifyvm $vm --nic2 hostonly --host-only-adapter2 $hostOnly
}

Write-Host "[+] Готово. Статические IP задаются внутри ВМ (см. docs/01-setup.md)."
