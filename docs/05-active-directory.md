# Контроллер домена и детекты AD-атак

Active Directory — главная цель в корпоративных сетях, поэтому отдельный блок стенда.
Это основа для будущего отдельного проекта по пентесту AD: здесь мы делаем **обнаружение**.

## Ресурсы

16 ГБ RAM не хватит на всё сразу. Для AD-блока держим включёнными:
**wazuh (4 ГБ) + dc01 (4 ГБ) + win10 в домене (3 ГБ)** ≈ 11 ГБ. Kali и NIDS на это время выключаем.

| ВМ | ОС | IP | Роль |
|----|----|----|------|
| dc01 | Windows Server 2019/2022 (eval) | 192.168.56.40 | контроллер домена `lab.local` |
| win10 | Windows 10 | 192.168.56.20 | рабочая станция в домене |

Server 2019/2022 — бесплатная evaluation-версия Microsoft (180 дней).

## Развёртывание

1. Установить роль AD DS, повысить до DC, домен `lab.local`.
2. Создать несколько пользователей, один сервисный аккаунт с SPN (мишень для Kerberoasting)
   и одного пользователя с флагом «не требовать предаутентификацию Kerberos» (мишень AS-REP).
3. Ввести win10 в домен.
4. Поставить Sysmon и Wazuh-агент на dc01 и win10 (тот же `install-agent.ps1`).
5. На dc01 включить расширенный аудит:

   ```
   auditpol /set /subcategory:"Kerberos Service Ticket Operations" /success:enable /failure:enable
   auditpol /set /subcategory:"Kerberos Authentication Service" /success:enable /failure:enable
   auditpol /set /subcategory:"Directory Service Access" /success:enable /failure:enable
   auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
   ```

   И собирать журнал Security агентом (в sysmon-modular/штатном наборе он обычно уже идёт;
   иначе добавить `<location>Security</location>` в ossec.conf агента dc01).

## Детекты

Правила — в [rules/wazuh/local_rules_ad.xml](../rules/wazuh/local_rules_ad.xml),
переносимые версии — в [rules/sigma/](../rules/sigma/) (файлы с префиксом `ad_`).

| Техника | ATT&CK | Телеметрия | Правило |
|---------|--------|-----------|---------|
| Kerberoasting | T1558.003 | 4769, шифрование RC4 (0x17) | 100300 |
| AS-REP roasting | T1558.004 | 4768 без предаутентификации | 100301 |
| DCSync | T1003.006 | 4662, GUID операции репликации | 100310 |
| Pass-the-Hash | T1550.002 | 4624 LogonType 9 / NTLM с привилег. аккаунта | 100320 |
| Перечисление через BloodHound | T1087.002 | всплеск 4661/4662 с одного хоста | 100330 |

## Как проверять

В отличие от Windows-блока, здесь **не используем реальные offensive-инструменты для кражи
учётных данных**. Телеметрию получаем безопасно:

- **Kerberoasting / AS-REP:** штатной утилитой — запрос сервисного билета RC4 к своему же
  тестовому SPN (`Add-Type` + класс `KerberosRequestorSecurityToken`). Это легитимный API,
  он порождает ровно событие 4769, на которое смотрит правило.
- **DCSync:** проверяем правило на историческом событии 4662 с GUID репликации
  (`1131f6aa-...` / `1131f6ad-...`) — его можно взять из документации и прогнать через
  `wazuh-logtest`, не выполняя саму атаку.
- **Pass-the-Hash / BloodHound:** отрабатываем на интерактивных/сетевых входах и обычном
  LDAP-переборе от тестовой учётки, фиксируя пороги.

Для каждого — запись в [матрицу покрытия](03-coverage.md) и, при желании, отдельный
отчёт об инциденте.
