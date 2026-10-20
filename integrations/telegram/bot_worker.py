#!/usr/bin/env python3
"""Telegram-бот-воркер: обрабатывает нажатия кнопок под алертами (пункт 10).

custom-telegram.py только шлёт алерты. Этот воркер принимает колбэки
«Взять в работу»/«Ложное срабатывание», отмечает их в локальном журнале триажа
и, опционально, создаёт/обновляет кейс в TheHive (связка с SOAR, пункт 12).

Запуск как служба (systemd) на отдельном хосте или на wazuh:
    TG_TOKEN=... python integrations/telegram/bot_worker.py

Зависимости минимальны: только стандартная библиотека (long polling getUpdates).
Токен — через переменную окружения, в git не коммитим.
"""
import json
import os
import sqlite3
import time
from pathlib import Path
from urllib import request, parse

TOKEN = os.environ.get("TG_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"
DB = Path(os.environ.get("TRIAGE_DB", "triage.db"))


def api(method: str, **params):
    data = parse.urlencode(params).encode()
    with request.urlopen(f"{API}/{method}", data=data, timeout=70) as resp:
        return json.loads(resp.read())


def init_db():
    con = sqlite3.connect(DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS triage ("
        "alert_id TEXT, status TEXT, analyst TEXT, ts INTEGER)"
    )
    con.commit()
    return con


def record(con, alert_id, status, analyst):
    con.execute(
        "INSERT INTO triage(alert_id,status,analyst,ts) VALUES (?,?,?,?)",
        (alert_id, status, analyst, int(time.time())),
    )
    con.commit()


def handle_callback(con, cq):
    data = cq.get("data", "")
    user = cq.get("from", {}).get("username") or cq.get("from", {}).get("first_name", "analyst")
    action, _, alert_id = data.partition(":")
    label = {"ack": "взято в работу", "fp": "помечено как ложное"}.get(action, data)
    record(con, alert_id, action, user)

    # Подтверждение в чат
    api("answerCallbackQuery", callback_query_id=cq["id"], text=f"OK: {label}")
    msg = cq["message"]
    new_text = msg.get("text", "") + f"\n\n— {label} ({user})"
    api("editMessageText", chat_id=msg["chat"]["id"],
        message_id=msg["message_id"], text=new_text)


def main():
    if not TOKEN:
        raise SystemExit("Задайте TG_TOKEN в окружении")
    con = init_db()
    offset = 0
    print("bot_worker запущен, ожидаю колбэки...")
    while True:
        try:
            resp = api("getUpdates", timeout=60, offset=offset)
        except Exception as exc:  # noqa: BLE001
            print("getUpdates error:", exc)
            time.sleep(5)
            continue
        for upd in resp.get("result", []):
            offset = upd["update_id"] + 1
            if "callback_query" in upd:
                handle_callback(con, upd["callback_query"])


if __name__ == "__main__":
    main()
