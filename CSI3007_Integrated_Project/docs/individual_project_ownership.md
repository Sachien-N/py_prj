# Individual Project Ownership

**These are three independently owned applications, not a jointly developed
team project.** Every name and registration number below is taken from the
verified source files (each project's `config.py`, README and dashboard
caption agree on the same owner).

| Identity | Full name | Registration No. | Application | Design system |
|---|---|---|---|---|
| Person A | **Sachien N** | **23MID0255** | Smart Expense Categorization and Budget Manager | Claymorphism |
| Person B | **Shravan N A** | **23MID0445** | Smart Subscription Manager | Glassmorphism |
| Person C | **Hariharan S** | **23MID0182** | Smart Home Electricity Monitoring and TNEB Bill Verification System | Neumorphism |

Course: **CSI3007 — Advanced Python Programming**.

## Evidence per project

- **Person A** — `person_a_sachien_n_23MID0255/config.py` declares
  `owner_name = "Sachien N"`, `owner_registration = "23MID0255"`; the README
  and the dashboard caption repeat the same identity; the API titles itself
  `Person A — Smart Expense API`.
- **Person B** — `person_b_shravan_n_a_23MID0445/config.py` declares
  `owner_name = "Shravan N A"`, `owner_registration = "23MID0445"`; the
  README header reads "Shravan N A · Registration No. 23MID0445"; the API
  titles itself `Person B — Smart Subscription API`.
- **Person C** — `person_c_hariharan_s_23MID0182/config.py` declares
  `owner_name = "HARIHARAN S"`, `owner_registration = "23MID0182"`; the
  README header reads "HARIHARAN S · Registration No. 23MID0182"; the API
  titles itself `Person C — Smart Electricity API`.

(The uppercase spelling in Person C's own files is preserved deliberately.)

## What ownership means in practice

1. **Database ownership.** Each application owns its SQLite file
   (`data/person_a.db`, `data/person_b.db`, `data/person_c.db`). No process
   other than the owning application ever opens that file. Cross-project
   numbers appear in a dashboard only after the owning API exported them
   through its documented endpoints.
2. **Business logic ownership.** Services live inside their project folder
   (`services/`); the integration layer in `integration/` contains only
   registry/health/landing-page code and never business rules.
3. **Visual identity ownership.** Each dashboard applies exactly one design
   system through its own `ui/theme.py`: Claymorphism (A), Glassmorphism
   (B), Neumorphism (C). The three dashboards are intentionally not three
   colour variants of one template.
4. **Independent executability.** Each project runs on its own (API + UI +
   DB + tests). Losing one project degrades only the specific integration
   features that reference it — documented per feature in
   `docs/api_contracts.md`.
