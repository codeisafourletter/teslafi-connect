# TeslaFi Connect

A focused first building block for this repository's original TeslaFi-integration idea: validate and inspect an **already saved TeslaFi JSON feed record** locally.

**Status: 0.1.0 prototype.** Python 3.10+ only. No account, token, package install, network request, or vehicle action is required or performed.

## Try it

From this source folder:

```bash
python -m teslafi_connect --input examples/status.json
```

The example is synthetic. To inspect your own saved record, substitute its path:

```bash
python -m teslafi_connect --input /path/to/saved-record.json
```

The result shows the source timestamp and available state, battery level, and charging state. VIN, location and account identity are omitted. Values retain their source types. A missing timestamp remains null; the tool never treats a successful parse as proof that data is live or infers timezone/age.

Supported input is a flat JSON feed object with at least one nonempty string `state`/`charging_state`, or a finite 0–100 `battery_level`. `Date` or `date` supplies the timestamp when present. API-error, empty, invalid, non-JSON, or oversized (>2 MiB) records fail clearly with exit code 1 without echoing private payloads. Success returns 0. This is not a historical CSV importer and does not claim universal compatibility with every TeslaFi export schema.

## Verify

```bash
python -m unittest discover -s tests -v
```

Six tests cover a custom local input, field preservation/privacy, missing timestamps, invalid/error records, response size, and failure exits. No live TeslaFi account was accessed. Real schema compatibility needs a saved owner record; the test suite does not pretend synthetic data proves live integration.

The former default branch was a placeholder. This small implementation establishes a tested parsing boundary without adding dashboards, credentials, vehicle controls, or an unrelated application. It is independent of the similarly named ChatGPT skill. No open-source license is granted; keep personal data outside Git.
