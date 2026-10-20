# План эмуляции техник ATT&CK

Все тесты выполняются **только на ВМ win10 стенда** после отката к снимку `atomic-ready`.

## Порядок работы с каждой техникой

1. Посмотреть доступные тесты: `Invoke-AtomicTest T1003.001 -ShowDetailsBrief`
2. Проверить зависимости: `Invoke-AtomicTest T1003.001 -TestNumbers N -CheckPrereqs`
3. Записать время запуска (UTC), выполнить: `Invoke-AtomicTest T1003.001 -TestNumbers N`
4. Найти событие в Wazuh → Threat Hunting, зафиксировать сработавшее правило (или его отсутствие)
5. Если правило не сработало, доработать `local_rules.xml` и проверить в `wazuh-logtest`
6. Откатить изменения: `Invoke-AtomicTest T1003.001 -TestNumbers N -Cleanup`
7. Обновить [матрицу покрытия](03-coverage.md)

Номера тестов меняются между версиями atomics, поэтому выбирайте их по названию из `-ShowDetailsBrief`.

## Серия 1: отдельные техники

| # | Техника | Тактика | Какой тест искать в `-ShowDetailsBrief` | Ожидаемое правило |
|---|---------|---------|------------------------------------------|-------------------|
| 1 | T1059.001 | Execution | Encoded command / Download cradle | 100100, 100101 |
| 2 | T1003.001 | Credential Access | Dump LSASS using comsvcs.dll | 100111, 100110 |
| 3 | T1053.005 | Persistence | Scheduled Task Startup Script | 100120, 100121 |
| 4 | T1547.001 | Persistence | Reg Key Run | 100130 |
| 5 | T1136.001 | Persistence | Create a new user in a command prompt | 100140 |
| 6 | T1098 | Persistence | Add user to local Administrators group | 100141 |
| 7 | T1070.001 | Defense Evasion | Clear Logs | 100150 |
| 8 | T1562.001 | Defense Evasion | Tamper with Windows Defender (PowerShell) | 100160 |
| 9 | T1082 / T1033 / T1016 | Discovery | System Information Discovery и др. | 100170 → 100171 |

## Серия 2: цепочка атаки (сценарий для отчёта)

Имитация действий атакующего после фишингового письма, выполняется вручную в одной сессии:

1. **Execution:** пользователь «запускает вложение» → PowerShell с закодированной командой (T1059.001)
2. **Discovery:** `whoami /all`, `systeminfo`, `ipconfig /all`, `net user`, `net localgroup administrators` (T1082, T1033, T1087.001)
3. **Persistence:** ключ Run и запланированная задача (T1547.001, T1053.005)
4. **Privilege / Account manipulation:** новый пользователь и добавление его в администраторы (T1136.001, T1098)
5. **Credential Access:** дамп LSASS через comsvcs.dll (T1003.001)
6. **Defense Evasion:** очистка журналов (T1070.001)

Задача аналитика: по алертам Wazuh восстановить хронологию и написать отчёт по шаблону
[reports/TEMPLATE.md](../reports/TEMPLATE.md). Отдельно оцените, сколько этапов цепочки было бы
пропущено без собственных правил.

## Серия 3: сетевые сценарии с Kali (расширение)

| Сценарий | Источник телеметрии на win10 | Что настроить |
|----------|------------------------------|---------------|
| Сканирование портов (`nmap -sS 192.168.56.20`) | Журнал брандмауэра Windows (`pfirewall.log`) | Включить журналирование отброшенных пакетов, добавить `localfile` в агент, правило на N соединений с одного IP |
| Подбор пароля RDP/SMB | Security 4625 | Штатные правила Wazuh на серию неудачных входов; проверить порог |
| Сетевые соединения процессов | Sysmon Event 3 | Правило на исходящие соединения PowerShell/rundll32 |
