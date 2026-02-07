# Risk Model

Each factor is scored 0-10, then combined with fixed weights:

- File system scope: 25%
- Network egress: 20%
- Shell execution: 25%
- Secrets exposure: 15%
- Skills/plugins: 15%

Tiers:

- 0.0-2.9: LOW
- 3.0-5.9: MEDIUM
- 6.0-8.9: HIGH
- 9.0-10.0: CRITICAL

The model is intentionally transparent and deterministic.
