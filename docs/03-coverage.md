# Матрица покрытия MITRE ATT&CK

Статусы: ✅ обнаружено · ⚠️ обнаружено частично / есть ложные срабатывания · ❌ не обнаружено · ⏳ не проверено

| Тактика | Техника | Wazuh rule | Sigma | Тест (Atomic) | Статус | Примечание |
|---------|---------|-----------|-------|---------------|--------|------------|
| Execution | T1059.001 PowerShell | 100100, 100101 | [encoded](../rules/sigma/proc_creation_win_powershell_encoded.yml) | | ⏳ | |
| Credential Access | T1003.001 LSASS Memory | 100110, 100111 | [lsass](../rules/sigma/proc_access_win_lsass_access.yml) | | ⏳ | |
| Persistence | T1053.005 Scheduled Task | 100120, 100121 | [schtasks](../rules/sigma/proc_creation_win_schtasks_suspicious.yml) | | ⏳ | |
| Persistence | T1547.001 Run Keys | 100130 | [run key](../rules/sigma/registry_set_win_run_key.yml) | | ⏳ | |
| Persistence | T1136.001 Local Account | 100140 | — | | ⏳ | |
| Persistence | T1098 Account Manipulation | 100141 | — | | ⏳ | |
| Defense Evasion | T1070.001 Clear Event Logs | 100150 | [clear log](../rules/sigma/proc_creation_win_clear_eventlog.yml) | | ⏳ | |
| Defense Evasion | T1562.001 Disable Tools | 100160 | — | | ⏳ | |
| Discovery | T1082 / T1033 / T1016 | 100170, 100171 | — | | ⏳ | |
| Recon (сеть) | T1046 / T1595 | 100200, 100201 | — | nmap с Kali | ⏳ | Suricata, docs/04 |
| Initial Access (веб) | T1190 | 100210 | — | атаки на Juice Shop | ⏳ | Suricata, docs/04 |
| Credential Access | T1558.003 Kerberoasting | 100300 | ad_kerberoasting | запрос TGS RC4 | ⏳ | AD, docs/05 |
| Credential Access | T1558.004 AS-REP roasting | 100301 | — | | ⏳ | AD, docs/05 |
| Credential Access | T1003.006 DCSync | 100310 | — | 4662 из logtest | ⏳ | AD, docs/05 |
| Lateral Movement | T1550.002 Pass-the-Hash | 100320 | — | | ⏳ | AD, docs/05 |
| Discovery (AD) | T1087.002 BloodHound | 100330, 100331 | — | LDAP-перебор | ⏳ | AD, docs/05 |

**Итог:** 0 / 16 техник подтверждено.

Для наглядности в резюме: экспортируйте слой в [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)
(раскрасьте покрытые техники) и приложите скриншот в README.
