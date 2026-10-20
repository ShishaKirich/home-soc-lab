# Сетевое обнаружение: Suricata → Wazuh (пункт 7)

Добавляем сетевую видимость (NDR) к имеющейся хостовой (EDR). Suricata слушает трафик
стенда, пишет события в `eve.json`, Wazuh их читает и коррелирует с хостовыми алертами.

## Где разместить сенсор

Самый простой и честный вариант — отдельная ВМ-сенсор `nids` (Ubuntu, 2 ГБ) со вторым
адаптером в той же host-only сети 192.168.56.0/24, слушающим в promiscuous-режиме. Либо
ставим Suricata прямо на ВМ `wazuh`, слушая её интерфейс eth1. Для учебного стенда
второго варианта достаточно.

## Установка (Ubuntu / Amazon Linux)

```bash
sudo add-apt-repository ppa:oisf/suricata-stable -y   # для Ubuntu
sudo apt-get update && sudo apt-get install -y suricata jq
sudo suricata-update                                  # базовый набор ET Open
sudo systemctl enable --now suricata
```

В `/etc/suricata/suricata.yaml`:
- `af-packet: interface: eth1` — интерфейс сети стенда;
- `HOME_NET: "[192.168.56.0/24]"`;
- в `outputs → eve-log` включить `alert`, `dns`, `http`, `flow`, `tls`.

## Свои правила

Файл [rules/suricata/local.rules](../rules/suricata/local.rules) подключается в
`suricata.yaml` (`rule-files: - local.rules`). Проверка: `sudo suricata -T -c /etc/suricata/suricata.yaml`.

## Интеграция с Wazuh

На менеджере/агенте, где лежит `eve.json`, добавить в `ossec.conf`:

```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/log/suricata/eve.json</location>
</localfile>
```

Штатные правила Wazuh уже разбирают Suricata (группа `suricata`, базовые ID около 86600).
Собственные корреляции — в [rules/wazuh/local_rules_network.xml](../rules/wazuh/local_rules_network.xml).

## Что проверить (атаки с Kali, 192.168.56.30)

| Сценарий с Kali | Правило Suricata | Корреляция в Wazuh |
|-----------------|------------------|--------------------|
| `nmap -sS -p- 192.168.56.20` | детект SYN-скана (порог flow) | серия алертов с одного src → один инцидент |
| `nmap -sV` / агрессивное сканирование | ET SCAN (из ET Open) | повышение уровня |
| Явный плейнтекст-пароль в HTTP на Juice Shop | свой sid на credential в URL | связать с хостовым алертом веб-атаки |

Так сетевой и хостовой слои показываются вместе — это ровно то, что делает SOC при разборе.
