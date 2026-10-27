# Project Overview

Course **CSI3007 — Advanced Python Programming** delivers three
**independently owned** Python applications that co-operate through
authenticated REST APIs. This repository integrates them for demonstration
while preserving their individual ownership, databases, business logic and
visual identities.

## The three projects

| | Person A | Person B | Person C |
|---|---|---|---|
| **Owner** | Sachien N | Shravan N A | Hariharan S |
| **Registration No.** | 23MID0255 | 23MID0445 | 23MID0182 |
| **Application** | Smart Expense Categorization and Budget Manager | Smart Subscription Manager | Smart Home Electricity Monitoring and TNEB Bill Verification System |
| **Design system** | Claymorphism | Glassmorphism | Neumorphism |
| **Backend** | FastAPI + SQLAlchemy on port 8001 | FastAPI + SQLAlchemy on port 8002 | FastAPI + SQLAlchemy on port 8003 |
| **Frontend** | Streamlit on port 8501 | Streamlit on port 8502 | Streamlit on port 8503 |
| **Database** | SQLite `data/person_a.db` | SQLite `data/person_b.db` | SQLite `data/person_c.db` |

## What each application does

**Person A — Smart Expense Categorization and Budget Manager.** Tracks
personal expenses with automatic category assignment, budget thresholds with
progress feedback, monthly and category reports, CSV export, and an
integration page that receives subscription expenses from Person B and
electricity expenses from Person C. The owner's dashboard is styled with the
soft, tactile Claymorphism system (pastel surfaces, rounded "clay" cards,
pill buttons).

**Person B — Smart Subscription Manager.** Manages recurring services:
billing cycles (weekly → custom), projected monthly/annual costs, renewal
calendar with reminders, payment history, CSV export, and an authenticated
push of subscription expense summaries to Person A. The dashboard uses the
Glassmorphism system: frosted translucent panels over a controlled indigo
gradient.

**Person C — Smart Home Electricity Monitoring and TNEB Bill Verification
System.** Records manual or simulated smart-socket readings, computes
interval energy, applies configurable progressive Tamil Nadu-style tariff
slabs, estimates period costs, compares estimates against actual TNEB bills,
and investigates discrepancies with up to six months of evidence. The system
*verifies* bills — it never claims the utility issued an incorrect bill. The
dashboard uses the Neumorphism system: soft raised/inset surfaces on a
single-tone grey canvas.

## Ownership model

The three applications are **not** a jointly owned team app. Each folder,
database, API, UI and test-suite belongs to exactly one student; names and
registration numbers are kept correct everywhere (see
`docs/individual_project_ownership.md`). Permitted data exchange happens
only through the documented, key-authenticated REST endpoints described in
`docs/api_contracts.md` — nobody reads another project's database.

## Repository map

```text
CSI3007_Integrated_Project/
├── start_all.py            # one-command launcher (7 services)
├── run_all.py              # original launcher (6 services, no gateway)
├── integration/            # gateway (port 8000) + registry + health checks
├── shared/                 # launcher/gateway utilities (not used by projects)
├── person_a_sachien_n_23MID0255/   # complete original application
├── person_b_shravan_n_a_23MID0445/ # complete original application
├── person_c_hariharan_s_23MID0182/ # complete original application
├── integration_tests/      # 9 live cross-project tests
├── tests/                  # repository-level tests
├── scripts/                # Windows/macOS setup + start scripts
└── docs/                   # this documentation set + originals in docs/original/
```
