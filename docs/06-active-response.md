# Активное реагирование Wazuh

Переход от «обнаружил» к «остановил»: по высокоуровневым алертам Wazuh сам выполняет
ответное действие. В лаборатории это безопасно, потому что сеть изолирована.

> ⚠️ Активное реагирование меняет состояние систем (блокирует IP, отключает учётки).
> Включать только на стенде. В проде такие действия согласуют и ограничивают whitelists.

## Сценарий 1. Блокировка IP при сетевом переборе/сканировании

Штатный скрипт `firewall-drop` добавляет src_ip во временный deny на хосте-жертве.
В `/var/ossec/etc/ossec.conf` менеджера:

```xml
<active-response>
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>100201,100003</rules_id>   <!-- серия сетевых алертов Suricata / штатный brute-force -->
  <timeout>600</timeout>               <!-- авторазблокировка через 10 минут -->
</active-response>
```

Проверка: с Kali запустить сканирование → правило 100201 → на win10 IP Kali блокируется →
через 10 минут снимается. Зафиксировать в отчёте время реакции (MTTR).

## Сценарий 2. Отключение учётки, созданной атакующим

Собственная команда реагирования: при срабатывании правила 100141 (добавление в локальные
администраторы) отключаем свежесозданную учётную запись на win10.

Скрипт [active-response/disable-user.ps1](../active-response/disable-user.ps1) кладётся в
`C:\Program Files (x86)\ossec-agent\active-response\bin\` на win10. Обёртка для Wazuh —
[active-response/disable-user.cmd](../active-response/disable-user.cmd).

В `ossec.conf` менеджера:

```xml
<command>
  <name>disable-user</name>
  <executable>disable-user.cmd</executable>
  <timeout_allowed>no</timeout_allowed>
</command>
<active-response>
  <command>disable-user</command>
  <location>local</location>
  <rules_id>100141</rules_id>
</active-response>
```

Wazuh передаёт в stdin скрипта JSON алерта; из него берём имя пользователя и отключаем его.

## Метрики

- MTTD (detection) и MTTR (response) по каждому сценарию.
- «Было/стало»: сколько времени у атакующего без реагирования и с ним.
- Риски автоматики: ложное срабатывание → блокировка легитимного админа (обосновать
  whitelist и короткий timeout).
