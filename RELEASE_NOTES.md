# 1.0.0-rc.2 — driving and charging workspace

The candidate expands from a status utility into a complete reporting journey:

- Local CSV/JSON history import with explicit mapping, single-activity export support, distance/currency/offset choices, and optional tariff.
- Date/activity filters, daily charts, known-vs-missing totals, equal-period distance comparisons, row-cited observations, and exportable report evidence.
- Responsive browser UI, clear memory-only storage policy, labeled synthetic demo, and separate current/last-good status panel using a loopback backend.
- Model regressions and full browser workflows at390/768/1440 px; status requests mocked, no private accounts accessed.

The read-only CLI remains compatible. No stable merge, package publication, deployment, vehicle control, or data migration. The history mapper accepts the documented normalized fields rather than claiming an undocumented universal TeslaFi export schema.

## Acceptance before1.0.0

All Python/model/browser CI must pass. An owner should validate one real export's columns, units, timestamp offsets and totals locally, and separately validate current/last-good feed shape. Unknowns and tariff estimates must remain labeled. Real-account historical fetching, mixed-unit inference, predictive/causal analysis and vehicle commands are outside this candidate.
