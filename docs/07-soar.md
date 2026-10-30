# SOAR: Wazuh → Shuffle → TheHive

Полный конвейер SOC: алерт автоматически превращается в кейс, обогащается данными об
угрозах и назначается аналитику.

```
 Wazuh Manager ──webhook──► Shuffle (orchestration) ──► TheHive (кейс-менеджмент)
       │                        │                              ▲
       │                        ├─► VirusTotal / AbuseIPDB (обогащение)
       │                        └─► Telegram (уведомление аналитику)
```

## Компоненты и ресурсы

TheHive и Shuffle прожорливы. На 16 ГБ RAM запускаем SOAR-блок **отдельно** от AD-блока:
**wazuh (4 ГБ) + soar (6–8 ГБ, Docker: Shuffle + TheHive + Cassandra/Elasticsearch)**.
win10 поднимаем для генерации одного-двух алертов, потом гасим.

ВМ `soar` (Ubuntu, Docker):
- Shuffle: `git clone https://github.com/Shuffle/Shuffle && cd Shuffle && docker compose up -d`
- TheHive 5: по официальному `docker-compose` из документации StrangeBee.

## Поток

1. **Wazuh → Shuffle.** На менеджере интеграция-вебхук шлёт алерты level ≥ 10 в Shuffle:

   ```xml
   <integration>
     <name>shuffle</name>
     <hook_url>http://192.168.56.50:3001/api/v1/hooks/webhook_<ID></hook_url>
     <level>10</level>
     <alert_format>json</alert_format>
   </integration>
   ```

2. **Shuffle-воркфлоу** (экспорт в [integrations/shuffle/workflow.json](../integrations/shuffle/workflow.json)):
   - принимает вебхук, парсит алерт;
   - если есть `data.src_ip` — запрос в AbuseIPDB; если есть хеш файла — в VirusTotal;
   - создаёт кейс в TheHive с observables (IP, хеш, хост, техника ATT&CK);
   - шлёт в Telegram ссылку на кейс.

3. **TheHive.** Аналитик ведёт кейс: задачи, наблюдаемые, вердикт. С ним связан
   триаж из Telegram-бота: колбэк «взять в работу» обновляет
   статус задачи через TheHive API.

## Демонстрируемый результат

- Сквозной сценарий: атака на win10 → алерт Wazuh → автокейс в TheHive с обогащением →
  уведомление в Telegram.
- Метрики: сколько ручной работы убрала автоматизация (время от алерта до готового кейса).

> API-ключи VirusTotal/AbuseIPDB и токены — только в переменных окружения/секретах Shuffle,
> не в `workflow.json` в git. В экспортированном воркфлоу значения заменены плейсхолдерами.
