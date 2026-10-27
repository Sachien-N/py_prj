# REST Integration Contract

This document is the authoritative integration contract for the three independent projects. Only JSON over HTTP is used. No project opens another project's SQLite file.

```text
Person B (subscriptions) ── authenticated POST ──► Person A (expenses)
Person C (electricity)  ── authenticated POST ──► Person A (expenses)
Person A can also pull the same documented payloads with an empty-body POST.
```

---

## 1. Services and development keys

| Service | URL | Credential |
|---|---|---|
| Person A API | `http://127.0.0.1:8001` | Accepts B and C keys on separate endpoints |
| Person B API | `http://127.0.0.1:8002` | Uses `PERSON_A_SYNC_API_KEY` for its push/payload endpoints |
| Person C API | `http://127.0.0.1:8003` | Uses `PERSON_A_SYNC_API_KEY` for its push/payload endpoints |

Matching development values in the supplied `.env` files:

| Direction | Header value | Person A variable | Sender variable |
|---|---|---|---|
| B → A / A pulls B | `dev-person-b-to-a-key` | `PERSON_B_SYNC_API_KEY` | B: `PERSON_A_SYNC_API_KEY` |
| C → A / A pulls C | `dev-person-c-to-a-key` | `PERSON_C_SYNC_API_KEY` | C: `PERSON_A_SYNC_API_KEY` |

Header:

```http
X-API-Key: <configured key>
Accept: application/json
```

- Wrong or missing keys return **HTTP 401** with a safe message.
- API keys are never included in payloads or user-facing errors.
- Change all keys before any shared deployment. These are local development credentials.

---

## 2. Person B → Person A

### 2.1 Trigger

- **Push (primary):** Person B calls `POST http://127.0.0.1:8001/integrations/subscriptions/sync` with its key.
- **Pull:** Person A calls `GET http://127.0.0.1:8002/integrations/person-a/payload` with the B key when its own `POST /integrations/subscriptions/sync` is called with an empty body.
- Person B's own endpoint is `POST http://127.0.0.1:8002/integrations/person-a/sync` (also authenticated).

### 2.2 Payload schema

```json
{
  "source_app": "person_b",
  "generated_at": "2026-10-21T10:05:00",
  "billing_period": "2026-10",
  "summary": {
    "active_subscriptions": 2,
    "expense_records": 2,
    "estimated_records": 1,
    "actual_records": 1,
    "monthly_costs_by_currency": {"INR": "2174.00"},
    "note": "Estimated records are recurring-cost shares, not confirmed payments. No payment provider is integrated."
  },
  "expense_records": [
    {
      "source_app": "person_b",
      "external_id": "sub:1:2026-10",
      "subscription_id": 1,
      "service_name": "Netflix",
      "category": "Entertainment",
      "amount": "499.00",
      "currency": "INR",
      "billing_period": "2026-10",
      "billing_date": "2026-10-15",
      "record_updated_at": "2026-10-21T10:05:00",
      "is_estimate": false,
      "description": "Recorded payment for Netflix (2026-10). Recorded manually in Person B; no payment provider was called."
    },
    {
      "source_app": "person_b",
      "external_id": "sub:2:2026-10",
      "subscription_id": 2,
      "service_name": "Adobe Creative Cloud",
      "category": "Software",
      "amount": "1675.00",
      "currency": "INR",
      "billing_period": "2026-10",
      "billing_date": "2026-10-31",
      "record_updated_at": "2026-10-20T18:00:00",
      "is_estimate": true,
      "description": "Estimated monthly recurring share for Adobe Creative Cloud (2026-10). Not an actual payment."
    }
  ]
}
```

Rules:

- `external_id` is stable per subscription and period: `sub:<subscription_id>:<YYYY-MM>`.
- If an actual payment exists for that subscription and billing period, its amount is sent with `is_estimate: false`; otherwise Person B sends the monthly-equivalent recurring-cost share with `is_estimate: true`.
- `record_updated_at` is an ISO-8601 timestamp from the local record.
- Amounts are decimal **strings** with two decimal places.
- No passwords, tokens or unrelated personal data are included.

### 2.3 Success response from Person A

```json
{
  "source": "person_b",
  "status": "success",
  "billing_period": "2026-10",
  "records_received": 2,
  "records_imported": 1,
  "records_updated": 1,
  "last_success_at": "2026-10-21T10:06:12.123456",
  "message": "Subscription expenses imported idempotently"
}
```

A repeated identical payload returns success with `records_imported: 0` and `records_updated` equal to the number of existing rows updated.

### 2.4 Person B's response after a successful push

```json
{
  "status": "success",
  "destination": "person_a",
  "period": "2026-10",
  "records_sent": 2,
  "last_success_at": "2026-10-21T10:06:12.123456",
  "person_a_response": {
    "source": "person_b",
    "status": "success",
    "records_received": 2,
    "records_imported": 2,
    "records_updated": 0
  }
}
```

### 2.5 Failure behaviour

If Person A is unreachable, times out, returns 5xx, or returns invalid JSON:

- Person B keeps all subscriptions and payments unchanged.
- The attempt is recorded in `integration_sync_state`: `status = failure`, attempt time, safe error text, HTTP status where available.
- Person B returns HTTP **503** (or **502** for an invalid upstream response) with safe details.
- The last successful timestamp is not overwritten.
- The user can retry at any time from **Person B → Integrations** or by calling the sync endpoint again.

Example failure body:

```json
{
  "detail": "Person A is unreachable; local subscription data is preserved. Local data is unchanged and you can retry the sync.",
  "details": {
    "destination": "person_a",
    "status": "failure",
    "period": "2026-10",
    "records_preserved": 2
  }
}
```

---

## 3. Person C → Person A

### 3.1 Trigger

- **Push:** Person C calls `POST http://127.0.0.1:8001/integrations/electricity/sync` with its key.
- **Pull:** Person A calls `GET http://127.0.0.1:8003/integrations/person-a/payload` with the C key when A's `POST /integrations/electricity/sync` is called with an empty body.
- Person C's own endpoint is `POST http://127.0.0.1:8003/integrations/person-a/sync`.

### 3.2 Payload schema

```json
{
  "source_app": "person_c",
  "generated_at": "2026-10-21T10:10:00+00:00",
  "summary": {
    "months": 6,
    "records": 2,
    "estimated_records": 1,
    "actual_records": 1,
    "total_amount_inr": "4640.00",
    "currency": "INR",
    "period_start": "2026-04-01",
    "period_end": "2026-10-21",
    "note": "Actual bills are used where recorded; otherwise configurable-tariff estimates are clearly marked."
  },
  "expense_records": [
    {
      "source_app": "person_c",
      "external_id": "electricity:2026-09",
      "period": "2026-09",
      "billing_date": "2026-09-30",
      "expense_amount": "2840.50",
      "currency": "INR",
      "units": "312.00",
      "is_estimate": false,
      "description": "Actual electricity bill TNEB-2026-09 for 2026-09-01 to 2026-09-30.",
      "record_updated_at": "2026-10-01T09:00:00",
      "data_coverage_pct": "96.40"
    },
    {
      "source_app": "person_c",
      "external_id": "electricity:2026-10",
      "period": "2026-10",
      "billing_date": "2026-10-31",
      "expense_amount": "1799.50",
      "currency": "INR",
      "units": "193.400",
      "is_estimate": true,
      "description": "Estimated electricity cost for 2026-10 using configured tariff “...”. This is not an actual bill. Reading coverage 71.20%.",
      "record_updated_at": "2026-10-21T10:10:00+00:00",
      "data_coverage_pct": "71.20"
    }
  ]
}
```

Rules:

- One record per month with a stable `external_id`: `electricity:<YYYY-MM>`.
- An actual bill whose billing period starts in the month takes precedence. Otherwise a configured-tariff estimate is used and marked `is_estimate: true`.
- Missing months with no readings and no bill are **not** included and are listed in `summary`/warnings by the Person C expense endpoint.
- `billing_date` is the bill date for actual bills, otherwise the last day of the month.
- `data_coverage_pct` reflects observed socket-reading intervals, not whole-house coverage.

### 3.3 Success response from Person A

```json
{
  "source": "person_c",
  "status": "success",
  "records_received": 2,
  "records_imported": 2,
  "records_updated": 0,
  "last_success_at": "2026-10-21T10:11:03.887651",
  "message": "Electricity expenses imported idempotently"
}
```

### 3.4 Failure behaviour

Same contract as B: HTTP 503 on unavailable/timeout, HTTP 502 for invalid upstream/receiver rejection, local readings/bills untouched, failure recorded, retry available, no fabricated amount.

---

## 4. Deduplication and idempotency

Person A owns an imported-expense audit table and a unique database constraint:

```text
UNIQUE(source_app, external_id)
```

| Source | `source_app` | `external_id` shape | Repeating the sync |
|---|---|---|---|
| Person B | `person_b` | `sub:<subscription_id>:<YYYY-MM>` | Updates the existing Person A expense; no duplicate. |
| Person C | `person_c` | `electricity:<YYYY-MM>` | Updates the existing Person A expense; no duplicate. |

Person B also enforces:

- `subscription_payments.idempotency_key` unique.
- `UNIQUE(subscription_id, billing_period)` to avoid a second recorded payment for the same subscription-month.
- A repeated payment request returns the existing payment with `deduplicated: true` and `created: false`.

Person C enforces `UNIQUE(socket_id, reading_at)` and rejects duplicate reading timestamps with HTTP 409.

Person A's imported expense rows are read-only in Person A; correction belongs at the source, followed by another idempotent sync.

---

## 5. Timeouts, retries and HTTP validation

| Setting | Default | Behaviour |
|---|---|---|
| `INTEGRATION_TIMEOUT_SECONDS` | 5 | Applied to every outbound integration request. |
| `INTEGRATION_RETRIES` | 2 | Retries connection errors, timeouts and HTTP 5xx with short backoff. |
| A pull timeout | 5 | Same setting. |
| Response validation | Pydantic | A validates the complete payload schema before importing. |
| HTTP status validation | 2xx expected | Anything else is recorded as a failed sync with a safe message. |

Retries do **not** apply to invalid credentials or 4xx validation errors. Request and response bodies are never written to logs in a way that exposes API keys.

---

## 6. Pulling from Person A

Person A can initiate the same flows:

```http
POST http://127.0.0.1:8001/integrations/subscriptions/sync
X-API-Key: dev-person-b-to-a-key

POST http://127.0.0.1:8001/integrations/electricity/sync
X-API-Key: dev-person-c-to-a-key
```

An empty body tells Person A to fetch:

```text
GET {PERSON_B_API_URL}/integrations/person-a/payload   (X-API-Key = B key)
GET {PERSON_C_API_URL}/integrations/person-a/payload   (X-API-Key = C key)
```

This is useful when Person B/C did not push, but it does not update Person B/C's own sync state. Their push endpoints do that.

---

## 7. Example commands

Using Python `requests` (recommended cross-platform):

```python
import requests

# Ask Person B to push its current-month data to Person A.
response = requests.post(
    "http://127.0.0.1:8002/integrations/person-a/sync",
    headers={"X-API-Key": "dev-person-b-to-a-key"},
    timeout=30,
)
print(response.status_code, response.json())

# Ask Person C to push six months of electricity expenses.
response = requests.post(
    "http://127.0.0.1:8003/integrations/person-a/sync",
    headers={"X-API-Key": "dev-person-c-to-a-key"},
    params={"start_date": "2026-05-01", "end_date": "2026-10-21"},
    timeout=60,
)
print(response.status_code, response.json())
```

Using cURL (quote the header on Windows):

```bash
curl -X POST "http://127.0.0.1:8002/integrations/person-a/sync" \
  -H "X-API-Key: dev-person-b-to-a-key"

curl -X POST "http://127.0.0.1:8003/integrations/person-a/sync?start_date=2026-05-01&end_date=2026-10-21" \
  -H "X-API-Key: dev-person-c-to-a-key"
```

Inspect imported rows:

```bash
curl "http://127.0.0.1:8001/expenses?source_app=person_b"
curl "http://127.0.0.1:8001/expenses?source_app=person_c"
curl "http://127.0.0.1:8001/integrations/status"
```

---

## 8. Test coverage of the contract

`integration_tests/` launches live Uvicorn servers against throwaway SQLite databases and verifies:

1. B → A subscription expense import.
2. C → A electricity expense import.
3. Repeating either request does not duplicate Person A rows.
4. Wrong/missing API keys return 401.
5. Invalid payloads return 422 and write nothing.
6. Person B remains healthy and preserves local data when Person A is unavailable (isolated live offline test).
7. B/C core functionality works without requiring A.
8. The three SQLite databases stay separate and contain disjoint table sets.
9. Health endpoints work for all three.
10. Monetary strings and date values remain consistent across the HTTP boundary.

Result at final verification: **9 passed**.
