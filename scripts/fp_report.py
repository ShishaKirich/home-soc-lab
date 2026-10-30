#!/usr/bin/env python3
"""Отчёт по ложным срабатываниям (False Positive) правил Wazuh.

Методика:
  1. Откатить win10 к снимку baseline-telemetry.
  2. Прожить на ВМ «обычный день» без атак (генератор фоновой активности —
     scripts/baseline_noise.ps1), 1-2 часа, НЕ запуская Atomic Red Team.
  3. Выгрузить алерты за этот период и прогнать через этот скрипт.

На вход подаётся Wazuh alerts.json (JSON lines) — его можно взять так:
    scp wazuh:/var/ossec/logs/alerts/alerts.json ./baseline-alerts.json
либо экспортом из Wazuh Dashboard → Discover за нужный интервал.

Скрипт считает срабатывания по нашим правилам (rule.id 100100-100199),
выводит таблицу «правило → число алертов за период → ставка шума в час»
и сохраняет fp_report.md для вставки в документацию.

    python scripts/fp_report.py baseline-alerts.json --hours 2
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

LAB_RULE_MIN, LAB_RULE_MAX = 100100, 100199


def load_alerts(path: Path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("alerts", type=Path, help="alerts.json (JSON lines)")
    ap.add_argument("--hours", type=float, default=1.0, help="длительность наблюдения, ч")
    ap.add_argument("--out", type=Path, default=Path("fp_report.md"))
    args = ap.parse_args()

    counts: Counter = Counter()
    descr: dict[str, str] = {}
    for a in load_alerts(args.alerts):
        rule = a.get("rule", {})
        try:
            rid = int(rule.get("id", -1))
        except (TypeError, ValueError):
            continue
        if LAB_RULE_MIN <= rid <= LAB_RULE_MAX:
            counts[str(rid)] += 1
            descr.setdefault(str(rid), rule.get("description", ""))

    lines = [
        "# Отчёт по ложным срабатываниям (базовая линия без атак)",
        "",
        f"Период наблюдения: {args.hours} ч. Активность: только фоновая, без Atomic Red Team.",
        "Любое срабатывание наших правил здесь — кандидат в ложные.",
        "",
        "| Rule ID | Описание | Алертов | Шум/час | Вердикт |",
        "|---------|----------|---------|---------|---------|",
    ]
    if not counts:
        lines.append("| — | срабатываний не зафиксировано | 0 | 0 | базовая линия чистая ✅ |")
    for rid, n in counts.most_common():
        rate = n / args.hours if args.hours else n
        verdict = "нужен тюнинг ⚠️" if rate >= 1 else "приемлемо"
        lines.append(f"| {rid} | {descr.get(rid,'')} | {n} | {rate:.1f} | {verdict} |")

    lines += [
        "",
        "## Как снижать шум",
        "- Добавить исключения (`negate`/`filter`) для легитимных процессов и путей.",
        "- Поднять порог/окно у частотных правил (`frequency`, `timeframe`).",
        "- Понизить `level` у информационных правил, оставив высокий только у коррелирующих.",
        "- Повторить замер после тюнинга и приложить сравнение «до/после».",
    ]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Готово: {args.out} (правил с шумом: {len(counts)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
