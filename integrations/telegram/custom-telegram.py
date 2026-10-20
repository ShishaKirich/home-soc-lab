#!/usr/bin/env python3
"""Интеграция Wazuh → Telegram (пункт 10).

Отправляет в чат алерты с level >= порога. В сообщении — кнопки колбэков
«Взять в работу» / «Ложное срабатывание» (их обрабатывает отдельный бот-воркер
integrations/telegram/bot_worker.py, использующий ваш опыт с ботами).

Установка на Wazuh Manager:
  1. Положить этот файл в /var/ossec/integrations/custom-telegram.py (chmod 750, owner root:wazuh).
  2. В ossec.conf:
       <integration>
         <name>custom-telegram</name>
         <level>10</level>
         <hook_url>https://api.telegram.org/bot<TOKEN>/sendMessage</hook_url>
         <api_key><CHAT_ID></api_key>
         <alert_format>json</alert_format>
       </integration>
  3. systemctl restart wazuh-manager

Wazuh вызывает скрипт так:
  custom-telegram.py <path_to_alert_json> <api_key(chat_id)> <hook_url>

Токен бота держать только в ossec.conf (доступ 640 root:wazuh), не коммитить в git.
"""
import json
import sys
from urllib import request, parse

LEVEL_EMOJI = {range(12, 16): "🔴", range(8, 12): "🟠", range(0, 8): "🟡"}


def pick_emoji(level: int) -> str:
    for rng, emoji in LEVEL_EMOJI.items():
        if level in rng:
            return emoji
    return "⚪"


def build_text(alert: dict) -> str:
    rule = alert.get("rule", {})
    agent = alert.get("agent", {})
    data = alert.get("data", {})
    level = int(rule.get("level", 0))
    mitre = ", ".join(rule.get("mitre", {}).get("id", [])) or "—"
    cmd = (
        data.get("win", {}).get("eventdata", {}).get("commandLine")
        or data.get("src_ip")
        or ""
    )
    lines = [
        f"{pick_emoji(level)} <b>Wazuh alert</b> (level {level}, rule {rule.get('id')})",
        f"<b>{rule.get('description','')}</b>",
        f"Хост: {agent.get('name','?')} ({agent.get('ip','?')})",
        f"MITRE: {mitre}",
        f"Время: {alert.get('timestamp','')}",
    ]
    if cmd:
        snippet = cmd if len(cmd) < 300 else cmd[:297] + "..."
        lines.append(f"<code>{snippet}</code>")
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 4:
        print("usage: custom-telegram.py <alert.json> <chat_id> <hook_url>", file=sys.stderr)
        return 1
    alert_file, chat_id, hook_url = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(alert_file, encoding="utf-8") as fh:
        alert = json.load(fh)

    alert_id = alert.get("id", "0")
    payload = {
        "chat_id": chat_id,
        "parse_mode": "HTML",
        "text": build_text(alert),
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "✅ Взять в работу", "callback_data": f"ack:{alert_id}"},
                {"text": "🚫 Ложное", "callback_data": f"fp:{alert_id}"},
            ]]
        }),
    }
    req = request.Request(
        hook_url,
        data=parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            resp.read()
    except Exception as exc:  # noqa: BLE001 — интеграция не должна валить wazuh-manager
        print(f"telegram send failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
