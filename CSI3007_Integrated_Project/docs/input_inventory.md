# Input Inventory and Archive Reconstruction Findings

**Date of analysis:** 2026-10-26 · **Environment:** Linux (Ubuntu) · Python 3.12.15

This document records exactly what was uploaded, what each archive actually
contained, how the original project tree was reconstructed, and what remains
uncertain. No content was fabricated: everything below was verified by
extracting and inspecting the uploads.

---

## 1. Uploaded files as received

The upload directory contained **five physical files**:

| File | Size (bytes) | SHA-256 (first 16 hex) | Integrity |
|---|---:|---|---|
| `Upload_Part_01.zip` | 41,931,286 | `17050c2ae5ef3252` | OK (`unzip -t`) |
| `Upload_Part_02.zip` | 40,483,563 | `6ace761fe508c4f6` | OK |
| `Upload_Part_03.zip` | 44,339,793 | `f0ee2e10a2e61906` | OK |
| `Upload_Part_04.zip` | 16,991,221 | `4295840e7f7f2bf8` | OK |
| `Three_Person_Python_Projects.zip` | 456,610 | `372e4cdf063fee02` | OK |

Sizes in KiB (40,948 / 39,535 / 43,300 / 16,593) match the upload report
exactly. **Note on the two identically named uploads:** the upload interface
listed `Three_Person_Python_Projects.zip` twice, but only **one** physical
copy exists in the upload directory — two same-named files evidently collided
into one path. Only the single copy above could be inspected; the comparison
requested for "two uploads" could therefore only be performed against the
reconstructed parts archive (see §4). Nothing was discarded.

## 2. The four outer archives (nested ZIPs)

Each `Upload_Part_XX.zip` is an ordinary ZIP **containing whole inner ZIP
files** (not split volumes, not 7z). Extracting them separately yielded the
complete original part set:

| Outer archive | Inner parts | Inner sizes (bytes) |
|---|---|---:|
| `Upload_Part_01.zip` | `Part_01.zip`, `Part_02.zip`, `Part_03.zip` | 13,392,625 / 14,506,936 / 14,486,873 |
| `Upload_Part_02.zip` | `Part_04.zip`, `Part_05.zip`, `Part_06.zip` | 17,919,169 / 11,350,498 / 11,733,859 |
| `Upload_Part_03.zip` | `Part_07.zip`, `Part_08.zip`, `Part_09.zip` | 16,122,276 / 14,105,175 / 14,462,952 |
| `Upload_Part_04.zip` | `Part_10.zip`, `Part_11.zip` | 11,750,105 / 5,447,847 |

**All 11 original parts are present and pass integrity checks.** No volumes
are missing or corrupted.

## 3. Format finding for Part_01–Part_11 (Case A, with a caveat)

Each part is an **independently extractable ZIP** (not a numbered volume).
However, the parts were created with **all directory paths stripped**: every
one of the 16,164 entries is a bare filename with no folder component. The
original hierarchy is therefore not recoverable from paths and had to be
rebuilt **from file contents** (fingerprints: database names, class names,
docstrings, ports, owner names, service imports).

Content classes found across the parts:

| Content class | Where | Share | Recoverable? |
|---|---|---|---|
| Virtualenv / site-packages (numpy, streamlit, PIL, pyarrow, tzdata, DLLs, protobuf, wheel metadata, ~14,000 package files incl. `pyvenv.cfg`) | Parts 02–10, also 01 | ~98 % of bytes | Not meaningfully — recreated via `requirements.txt` |
| Project source code + tests (3 projects) | Part_01, Part_11 | ~110 files | **Yes — reconstructed** |
| Databases `person_a.db` (69.6 KB), `person_b.db` (61.4 KB), `person_c.db` (3.98 MB) | Part_11 | 3 files | **Yes — recovered** |
| Root docs: `README.md` (22.3 KB), `INTEGRATION.md` (12.8 KB), `RUN_GUIDE_A_WINDOWS_BC_MACOS.txt` (33.5 KB), `requirements-all.txt`, `pytest.ini`, `run_all.py`, `.gitignore` | Part_01 | 7 files | **Yes — reconstructed** |

Timestamps inside the parts range 21:40–23:24 (2026-10-21).

## 4. The `Three_Person_Python_Projects.zip` upload — identity and comparison

The single uploaded copy contains a **previously modified / refactored
variant** of the same three projects (uploaded 2026-10-21 16:10–17:05, i.e.
*earlier* than the parts' file timestamps):

| Aspect | Parts tree (authoritative) | TPI zip (modified variant) |
|---|---|---|
| Structure | Specialised per-project services (e.g. `category_service`, `csv_service`, `report_service`, `billing`, `payment_service`, `socket_service`, `cost_service`, `bill_service`, `demo_service`, adapters) | Uniform template for all three (`api/app/auth/config/database/models/schemas/services/integration_service/ui/scripts`) |
| Auth | API-key headers only (no `auth.py`) | Adds `auth.py` module |
| Streamlit theming | Per-project `.streamlit/config.toml` (teal / indigo / amber) | Not present |
| Databases | `person_a.db`, `person_b.db`, `person_c.db` shipped | Only `person_a_expense.db` stub |
| Tests | A=16, B=13, C=16 + 9 live integration tests | Similar counts, different internals |
| File timestamps | 21:40–23:24 | 16:10–17:05 |

Sample content hashes confirm the trees differ (e.g. Person A `api.py`:
19,270 B in TPI vs 10,964 B in parts). **Decision:** the reconstructed parts
tree is treated as the authoritative original; the TPI zip is retained as a
reference variant only. No file from TPI overwrote a parts-tree file.

## 5. Reconstruction result (110 files)

`Three_Person_Python_Projects/` was rebuilt from the parts into the integrated
repository. Every placement was verified by content, and the result was
validated functionally:

- All 110 mapped files copied; **0 missing sources**.
- All Python files pass `py_compile`.
- Per-project suites: **A 16 passed, B 13 passed, C 16 passed** — exactly the
  counts documented in the original root README ("tests/ # 16 tests" etc.).
- Live cross-project integration tests: **9 passed** (servers spawned on
  isolated ports with temporary databases).

Mapping corrections discovered *by the tests* and applied:
`test_integration_exports.py` → Person C (imports C's `test_bills_analysis`),
`test_billing.py` → Person B (tests B's `services/billing.py`),
`demo_service.py` added to Person C's services (imported by C's `api.py`).

Known ambiguities (content-identical or interchangeable, functionally
irrelevant): the three near-identical `errors.py` variants and the three
`services/common.py` variants were assigned by docstring/marker match; the
`ui/__init__.py` of Person C is an empty file (the only empty variant left).

## 6. Secrets review

- `.env` files found in the parts contain **only local development values**:
  `dev-person-b-to-a-key` style placeholders and `<PASTE_..._HERE>` tokens.
  No real credentials exist in any upload.
- The final repository ships `.env.example` templates only; `.env` files are
  excluded and are recreated by the setup scripts.

## 7. Honest limitations

1. Only **one** physical `Three_Person_Python_Projects.zip` upload existed;
   the "two uploads" comparison (§4) was performed against the parts archive.
2. The flattened path layout means file-to-folder placement is inferred from
   content. Validation was functional (tests + compile + runtime), which is
   strong but not byte-level proof of the original layout.
3. The ~136 MB of virtualenv content in the parts was intentionally not
   "reconstructed"; it is recreated by `pip install -r requirements.txt`
   (all pins resolve on Python 3.11–3.13).
4. `run_all.cpython-313.pyc` exists in Part_11 but its source `run_all.py`
   is present in Part_01, so no decompilation was needed.
