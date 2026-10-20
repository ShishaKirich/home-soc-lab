# Развёртывание стенда

Ресурсы хоста: 16 ГБ RAM, около 35 ГБ на диске под новую ВМ Wazuh.
Одновременно держите включёнными не больше трёх ВМ (4 + 3 + 2 ГБ RAM).

## Шаг 0. Подготовить существующие ВМ

Существующие `jusyshop` (Windows 10) и `kali` используются повторно. Скрипт сам делает
снимок `before-soc-lab`, так что вернуться к исходному состоянию можно в любой момент.

## Шаг 1. Импорт Wazuh

1. Скачайте OVA с официальной страницы: <https://documentation.wazuh.com/current/deployment-options/virtual-machine/virtual-machine.html>
   (только с `packages.wazuh.com`).
2. Импорт (имя ВМ `wazuh`, 4 ГБ RAM вместо стандартных 8):

   ```powershell
   & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" import .\wazuh-4.x.y.ova --vsys 0 --vmname wazuh --memory 4096 --cpus 2
   ```

3. Логин в консоль ВМ и в Dashboard: учётные данные по умолчанию указаны на той же странице документации.
   **Сразу смените оба пароля.**

## Шаг 2. Сеть

На хосте при выключенных ВМ:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-network.ps1
```

Внутри ВМ задайте статические адреса на втором адаптере (host-only):

| ВМ    | IP              | Как задать |
|-------|-----------------|------------|
| wazuh | 192.168.56.10/24 | `/etc/sysconfig/network-scripts/ifcfg-eth1`: `BOOTPROTO=static`, `IPADDR=192.168.56.10`, `NETMASK=255.255.255.0`, `ONBOOT=yes`; затем `sudo systemctl restart network` |
| win10 | 192.168.56.20/24 | `New-NetIPAddress -InterfaceAlias "Ethernet 2" -IPAddress 192.168.56.20 -PrefixLength 24` |
| kali  | 192.168.56.30/24 | `sudo nmcli con mod "Wired connection 2" ipv4.method manual ipv4.addresses 192.168.56.30/24 && sudo nmcli con up "Wired connection 2"` |

Проверка: с хоста откройте `https://192.168.56.10` (Wazuh Dashboard).

## Шаг 3. Агент и Sysmon на Windows

Скопируйте `scripts/install-agent.ps1` в ВМ и запустите от администратора:

```powershell
powershell -ExecutionPolicy Bypass -File .\install-agent.ps1 -WazuhVersion 4.x.y-1
```

Убедитесь, что агент `win10-lab` в Dashboard → Agents имеет статус **Active**, а в
Threat Hunting видны события `data.win.system.channel: Microsoft-Windows-Sysmon/Operational`.

Сделайте снимок ВМ: `baseline-telemetry`.

## Шаг 4. Собственные правила

Скопируйте [rules/wazuh/local_rules.xml](../rules/wazuh/local_rules.xml) на менеджер:

```bash
sudo cp local_rules.xml /var/ossec/etc/rules/local_rules.xml
sudo chown wazuh:wazuh /var/ossec/etc/rules/local_rules.xml
sudo /var/ossec/bin/wazuh-analysisd -t        # проверка синтаксиса
sudo systemctl restart wazuh-manager
```

Отладка правила: `sudo /var/ossec/bin/wazuh-logtest`, затем вставьте JSON события из архива
(`/var/ossec/logs/archives/archives.json`, включается через `<logall_json>yes</logall_json>` в `ossec.conf`).

## Шаг 5. Atomic Red Team на Windows

Atomic Red Team (Red Canary) — набор безопасных тестов для эмуляции отдельных техник ATT&CK.
Используйте его **только в изолированной лабораторной ВМ**.

```powershell
# от администратора, внутри win10
Set-ExecutionPolicy Bypass -Scope Process -Force
IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
Install-AtomicRedTeam -getAtomics
Import-Module "C:\AtomicRedTeam\invoke-atomicredteam\Invoke-AtomicRedTeam.psd1"
```

Defender может удалять файлы атомиков. Добавьте исключение **только для `C:\AtomicRedTeam`**,
не отключайте защиту целиком: срабатывания Defender тоже являются полезной телеметрией.

Снимок ВМ: `atomic-ready`. Перед каждой серией тестов откатывайтесь к нему.
