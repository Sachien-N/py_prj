# Database Design

## Ownership and isolation

| Database | Owner | Location | Size shipped |
|---|---|---|---:|
| `person_a.db` | Person A only | `person_a_sachien_n_23MID0255/data/` | 69.6 KB |
| `person_b.db` | Person B only | `person_b_shravan_n_a_23MID0445/data/` | 61.4 KB |
| `person_c.db` | Person C only | `person_c_hariharan_s_23MID0182/data/` | 3.98 MB |

No application ever opens another project's database file. Cross-project
numbers arrive exclusively as validated JSON through the documented APIs and
are stored in the **receiver's own** tables with provenance columns
(`source_app`, `external_id`).

## Engine and conventions (all three projects)

- SQLite via SQLAlchemy 2.0 with WAL-friendly settings and **foreign keys
  enabled** per connection (`PRAGMA foreign_keys = ON`).
- Timestamps stored as **naive UTC**; Person C adds `to_naive_utc` /
  `from_naive_utc` plus local-day helpers (IST) for electricity intervals.
- Money and units use `Decimal` end-to-end (Pydantic validates decimal
  strings) to avoid float drift.
- Tables are created by `init_db()` when the API starts; Person A also seeds
  default categories there. Deleting `data/*.db` is therefore a safe reset —
  **it is never done silently** by any script.

## Main tables

**Person A** — `categories` (name unique, colour, is_default),
`expenses` (date, amount, category FK, payment_method, note, transaction_type,
`source_app`, `external_id` unique-pair for imports, `is_estimated`,
`record_updated_at`), `budgets` (category FK, month, limit_amount),
`integration_sync_state` (source_app, last_success_at, last_failure_at,
items_received).

**Person B** — `subscriptions` (service_name, category, amount, currency,
billing_cycle, custom_cycle_days, next_renewal, reminder_days, active),
`payments` (subscription FK, amount, paid_on, method, note),
`integration_sync_state` (push status toward A).

**Person C** — `sockets` (name, appliance, rated_power_w, is_demo),
`readings` (socket FK, ts_utc, cumulative_kwh, is_simulated),
`tariffs` (name, effective_from) with `tariff_slabs` (upper_bound_units,
rate_per_unit) and `tariff_components` (fixed_charge, duty_per_unit...),
`bills` (bill_month, units, amount, source, issued_on, is_demo),
`bill_comparisons` (bill FK, estimated_amount/units, discrepancy_percent,
verdict, checked_at), plus electricity expense staging for A payloads.

## Constraints, indexes and integrity

- Unique constraints: category name per project; `(source_app, external_id)`
  on imported expenses; tariff slab bounds per tariff.
- Foreign keys enforce relational integrity (e.g. deleting a socket removes
  nothing silently — the API refuses or cascades explicitly per route).
- Parameterised queries everywhere via SQLAlchemy ORM/`text()` bindings; no
  string-built SQL from user input.

## Demonstration data

The shipped databases contain **clearly labelled demonstration data**
(Person C's seeded sockets/readings/bills carry `is_demo` / `SIMULATED`
markers; the demo seed endpoint re-creates them on demand:
`POST /demo/seed`). For a clean start on a demo machine:

```bash
# stop the services, then (optional) reset one project's DB:
rm person_c_hariharan_s_23MID0182/data/person_c.db
python -m uvicorn api:app --port 8003   # re-creates the schema on start
curl -X POST http://127.0.0.1:8003/demo/seed -H 'Content-Type: application/json' \
     -d '{"months": 3, "force": true}'
```

## Backup and restore

SQLite files are single-file databases: with all services **stopped**, copy
`data/person_*.db` anywhere (e.g. `backup_2026-10-26/`); restoring is copying
the file back. While services run, use `sqlite3 data/person_a.db
".backup 'backup/person_a.db'"` for a consistent online snapshot.
