# 🛡️ Home SOC Lab — Wazuh · Sysmon · Suricata · Active Directory · SOAR

![status](https://img.shields.io/badge/status-active-success)
![focus](https://img.shields.io/badge/focus-Blue%20Team%20%2F%20Detection%20Engineering-blue)
![SIEM](https://img.shields.io/badge/SIEM-Wazuh-informational)
![framework](https://img.shields.io/badge/mapped%20to-MITRE%20ATT%26CK-red)

Домашняя лаборатория центра мониторинга ИБ (SOC), построенная по принципу **Detection-as-Code**.
Отрабатывается полный цикл работы аналитика:

> **эмуляция техники атакующего → сбор телеметрии → правило обнаружения → автоматическое реагирование → расследование → отчёт**

Каждый детект привязан к матрице **MITRE ATT&CK**, покрыт unit-тестами и проверяется в CI.
Отдельный блок сопоставляет меры стенда с требованиями **ГОСТ Р 57580.1** (защита информации
в финансовых организациях).

### Чему посвящён проект

| Направление | Технологии |
|-------------|-----------|
| SIEM и хостовая телеметрия (EDR) | Wazuh, Sysmon (sysmon-modular), журналы Windows/Linux |
| Эмуляция атак (purple team) | Atomic Red Team, MITRE ATT&CK |
| Detection Engineering | правила Wazuh (XML) + Sigma, unit-тесты, CI (GitHub Actions) |
| Сетевое обнаружение (NDR) | Suricata IDS |
| Защита Active Directory | детекты Kerberoasting, DCSync, Pass-the-Hash, BloodHound |
| Реагирование (SOAR) | Wazuh Active Response, Shuffle, TheHive, Telegram-бот |
| Соответствие регулятору | ГОСТ Р 57580.1, Wazuh SCA (CIS) |

> ⚠️ **Образовательный проект.** Все атаки выполняются исключительно в изолированной
> виртуальной сети (host-only), на собственных учебных ВМ. Проект посвящён **защите и
> обнаружению**, а не нападению.

## Архитектура

```
                 Host-only сеть 192.168.56.0/24 (изолирована от домашней сети)
 ┌─────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────┐
 │  wazuh  .56.10      │   │  win10 (jusyshop) .56.20 │   │  kali  .56.30       │
 │  Wazuh Manager      │◄──│  Wazuh Agent + Sysmon    │◄──│  источник атак      │
 │  Indexer, Dashboard │   │  Atomic Red Team         │   │  (Nmap, Hydra, ...) │
 └─────────────────────┘   └──────────────────────────┘   └─────────────────────┘
```

| ВМ     | ОС                  | RAM  | Роль                                   |
|--------|---------------------|------|----------------------------------------|
| wazuh  | Amazon Linux 2 (OVA)| 4 ГБ | SIEM: сбор, корреляция, дашборды       |
| win10  | Windows 10          | 3 ГБ | конечная точка-«жертва», телеметрия    |
| kali   | Kali Linux          | 2 ГБ | внешний атакующий (сетевые сценарии)   |
| dc01   | Windows Server (eval)| 4 ГБ | контроллер домена `lab.local` (блок AD) |
| soar   | Ubuntu + Docker     | 6–8 ГБ | Shuffle + TheHive (блок SOAR)        |

На 16 ГБ RAM все ВМ одновременно не запускаются. Блоки AD и SOAR включаются по очереди
(подробности в соответствующих docs); базовый блок — wazuh + win10 + kali.

## Структура репозитория

| Путь | Содержимое |
|------|------------|
| [docs/01-setup.md](docs/01-setup.md) | Пошаговое развёртывание стенда |
| [docs/02-attack-plan.md](docs/02-attack-plan.md) | План эмуляции техник ATT&CK |
| [docs/03-coverage.md](docs/03-coverage.md) | Матрица покрытия: техника → правило → статус |
| [docs/04-suricata-nids.md](docs/04-suricata-nids.md) | Сетевое обнаружение: Suricata → Wazuh |
| [docs/05-active-directory.md](docs/05-active-directory.md) | Контроллер домена и детекты AD-атак |
| [docs/06-active-response.md](docs/06-active-response.md) | Автоматическое реагирование Wazuh |
| [docs/07-soar.md](docs/07-soar.md) | SOAR-конвейер Wazuh → Shuffle → TheHive |
| [docs/08-gost-57580.md](docs/08-gost-57580.md) | Соответствие ГОСТ Р 57580.1 и hardening (SCA) |
| [scripts/](scripts/) | Настройка сети, установка агента, замер ложных срабатываний |
| [rules/wazuh/](rules/wazuh/) | Правила Wazuh: хост, сеть (Suricata), Active Directory |
| [rules/sigma/](rules/sigma/) | Те же детекты в формате Sigma (переносимы в любой SIEM) |
| [rules/suricata/](rules/suricata/) | Сетевые правила Suricata |
| [tests/](tests/) | Unit-тесты правил (фикстуры событий + движок проверки) |
| [active-response/](active-response/) | Скрипты активного реагирования |
| [integrations/](integrations/) | Telegram-бот и Shuffle-воркфлоу (SOAR) |
| [sca/](sca/) | Политика SCA и карта соответствия ГОСТ |
| [reports/](reports/) | Шаблон отчёта о расследовании инцидента |
| [.github/workflows/](.github/workflows/) | CI: валидация правил и прогон тестов |

## Инженерная практика (Detection-as-Code)

- **CI** ([validate-rules.yml](.github/workflows/validate-rules.yml)): при каждом коммите
  проверяется синтаксис Sigma и XML Wazuh и прогоняются unit-тесты правил.
- **Тесты** ([tests/](tests/)): на образцах событий проверяется, что правило срабатывает на
  атаке и молчит на легитимной активности. Локальный запуск: `python tests/run_tests.py`.
- **Ложные срабатывания** ([scripts/fp_report.py](scripts/fp_report.py)): замер шума правил
  на «обычном дне» без атак и тюнинг по результатам.
