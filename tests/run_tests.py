#!/usr/bin/env python3
"""Unit-тесты правил обнаружения (Detection-as-Code).

Идея: храним образцы событий (tests/events/*.json) и ждём, что каждое Sigma-правило
срабатывает на «злых» событиях и молчит на «чистых». Полноценный Wazuh в CI не поднимаем —
реализован компактный матчер для тех модификаторов Sigma, что используются в проекте
(endswith, startswith, contains, re, windash и логика condition вида "all of selection_*").

На живом стенде те же события стоит дополнительно прогнать через wazuh-logtest —
это проверяет уже XML-правила Wazuh, а не только Sigma.

Запуск:  python tests/run_tests.py
Выход:   0 — все тесты прошли, 1 — есть падения.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SIGMA_DIR = ROOT / "rules" / "sigma"
EVENTS_DIR = Path(__file__).resolve().parent / "events"


# ---------- матчинг одного поля ----------

def _as_list(v):
    return v if isinstance(v, list) else [v]


def _match_scalar(event_val, pattern, modifiers) -> bool:
    if event_val is None:
        return False
    ev = str(event_val)
    pat = str(pattern)
    if "re" in modifiers:
        return re.search(pat, ev) is not None
    variants = [pat]
    if "windash" in modifiers:
        # Sigma windash: '-' эквивалентен '/', '--', '—', '–'
        variants = {pat}
        for dash in ("/", "--", "—", "–"):
            variants.add(re.sub(r"(?<=\s)-", dash, pat))
            variants.add(pat.replace("-", dash, 1))
        variants = list(variants)
    ci = True  # Sigma строки регистронезависимы по умолчанию
    evl = ev.lower() if ci else ev
    for var in variants:
        v = var.lower() if ci else var
        if "contains" in modifiers and v in evl:
            return True
        if "endswith" in modifiers and evl.endswith(v):
            return True
        if "startswith" in modifiers and evl.startswith(v):
            return True
        if not ({"contains", "endswith", "startswith"} & set(modifiers)) and evl == v:
            return True
    return False


def _match_field(event, key, values) -> bool:
    field, *mods = key.split("|")
    modifiers = set(mods)
    ev = event.get(field)
    for pat in _as_list(values):
        for single in _as_list(ev) if isinstance(ev, list) else [ev]:
            if _match_scalar(single, pat, modifiers):
                return True
    return False


def _match_selection(event, selection) -> bool:
    if isinstance(selection, list):  # список словарей = OR
        return any(_match_selection(event, s) for s in selection)
    # все ключи в словаре соединяются по AND
    return all(_match_field(event, k, v) for k, v in selection.items())


# ---------- матчинг condition ----------

def _eval_condition(event, detection) -> bool:
    cond = detection["condition"].strip()
    sels = {k: v for k, v in detection.items() if k != "condition"}

    def sel_result(name):
        return _match_selection(event, sels[name])

    def group(prefix):
        return [sel_result(n) for n in sels if n.startswith(prefix)]

    # Поддерживаем ограниченный, но достаточный для проекта набор форм condition.
    if cond == "selection":
        return sel_result("selection")
    if cond.startswith("all of selection_"):
        return all(group("selection"))
    if cond.startswith("1 of selection_") or cond.startswith("any of selection_"):
        return any(group("selection"))
    m = re.match(r"^(\w+) and not (\w+)$", cond)
    if m:
        return sel_result(m.group(1)) and not sel_result(m.group(2))
    raise ValueError(f"condition не поддержан матчером: {cond!r}")


# ---------- прогон ----------

def load_rules():
    rules = {}
    for f in sorted(SIGMA_DIR.glob("*.yml")):
        rules[f.name] = yaml.safe_load(f.read_text(encoding="utf-8"))
    return rules


def main() -> int:
    rules = load_rules()
    cases = sorted(EVENTS_DIR.glob("*.json"))
    if not cases:
        print("Нет фикстур в tests/events/")
        return 1

    passed = failed = 0
    for case_file in cases:
        case = json.loads(case_file.read_text(encoding="utf-8"))
        rule_file = case["rule"]
        expect = case["expect"]          # "match" | "nomatch"
        event = case["event"]
        if rule_file not in rules:
            print(f"FAIL {case_file.name}: правило {rule_file} не найдено")
            failed += 1
            continue
        got = _eval_condition(event, rules[rule_file]["detection"])
        ok = (got and expect == "match") or (not got and expect == "nomatch")
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"{status} {case_file.name:45} [{rule_file}] expect={expect} got={'match' if got else 'nomatch'}")

    print(f"\nИтого: {passed} прошло, {failed} упало")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
