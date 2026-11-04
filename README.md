# TeslaFi Connect — driving and charging reports

**1.0.0-rc.2** is a local browser workspace for understanding owned driving/charging exports. Import history, confirm its columns and units, explore trends, inspect the contributing records, and export a report with provenance. A separate read-only panel can request the current logged status through a credential-safe local backend.

## Open the product

Python 3.10+ is the only runtime dependency. From this checkout:

```bash
python -m teslafi_connect --serve
```

Open **http://127.0.0.1:8768**. **Explore a demo report** uses clearly labeled fictional history. **Open history CSV or JSON** accepts your owned export; imports are never uploaded.

1. Map the start timestamp and activity type columns. For a drive-only or charge-only export, choose **All rows are drives/charges** instead of inventing a type column.
2. Map available distance, charging energy and cost columns; leave unavailable fields blank. Confirm distance units, currency, and offset for timestamps without a zone.
3. Build the report. Filter dates/activity, inspect daily distance/energy/cost, and follow insight links to source records.
4. Set both dates to compare known distance with the previous equal-length period. Incomplete exports are explicitly caveated; no causal explanation is invented.
5. Export filtered records, totals, original rows, source-file SHA-256, mapping and assumptions as JSON. Clear the workspace when finished.

## Supported historical data contract

TeslaFi's **current feed is not historical data**. This app does not manufacture trips or charges from snapshots, scrape an authenticated site, or claim a universal TeslaFi export schema. Its column mapper supports owned CSV files and flat JSON arrays that can express the following documented normalized fields:

| Field | Accepted values |
|---|---|
| Activity | `drive`, `trip`, `driving`, `charge`, `charging`, `charge session`, or one fixed activity for the whole file |
| Start | ISO-style date/time, e.g. `2025-01-01T08:30:00Z`, `2025-01-01 08:30:00`, or `2025-01-01` |
| Distance | Nonnegative numeric value; choose km or miles; used only for drives |
| Energy | Nonnegative kWh; used only for charges |
| Cost | Nonnegative amount in the selected currency; used only for charges |

CSV needs a unique, nonempty header and consistent column count; quoting and commas inside quoted fields are supported. JSON needs a nonempty array of flat records. Limits:20 MiB and100,000 records. If an export uses another date format, nested records, mixed units or currencies, normalize/split it first. Row citations are **1-based data record indices**, not physical CSV line numbers (a quoted field can span lines). Invalid timestamps/types are excluded with diagnostics; unknown numeric values remain unknown, not zero.

Recorded charge cost takes priority. An optional tariff estimates only missing charge costs with known kWh; estimates stay labeled. No gas-savings, charger-efficiency, billing-tax, or causal claims are made. Fixed timestamp offsets do not infer daylight-saving rules; split/normalize dates if an export spans offset changes. All charts and filters use UTC. The report stores every mapping and assumption.

## Optional logged status

The report UI works without an account. For current status, get a feed token while signed in at <https://www.teslafi.com/api.php> and set it locally before starting the server:

```bash
read -rsp 'TeslaFi API token: ' TESLAFI_API_TOKEN; echo
export TESLAFI_API_TOKEN
python -m teslafi_connect --serve
# After stopping the server:
unset TESLAFI_API_TOKEN
```

Click **Read logged status** or **Read last complete record** only when you want a read request. The token remains server-side and is sent only in the HTTPS Authorization header to the documented feed endpoint. The server binds127.0.0.1 and validates Host/Origin. No token goes to JavaScript, no vehicle controls exist, redirects are rejected, requests have a20-second timeout/2 MiB limit, and there are no automatic retries.

A logged timestamp may be old or have an unknown timezone. The panel preserves it and makes no freshness guarantee. The client requires a valid recognized status field rather than treating an empty/error-shaped response as success. Live account compatibility still needs owner acceptance; no private account was accessed during development.

The CLI remains available:

```bash
python -m teslafi_connect --fixture examples/status.json
python -m teslafi_connect --last-good
```

## Privacy and testing

History exists only in browser memory until reload/clear. No localStorage, analytics, external scripts or history uploads. Exported reports remain on your device and can contain private travel information. Original-file hashes identify inputs, not authenticity.

```bash
python -m unittest discover -s tests -v
npm ci
npm run test:web
npx playwright-core install chromium
npm run test:browser
```

Node22+ is for development only. Browser journeys test phone/tablet/desktop imports, mapping, date/type filters, unknown costs, tariff estimates, export and clear. Status responses are intercepted/mocked in browser tests; server test processes remove the token environment variable. No live requests are needed for verification.

See [RELEASE_NOTES.md](RELEASE_NOTES.md). This client is independent of the similarly named ChatGPT skill. No open-source license is granted.

For large imports, the UI bounds rendered rows to500 (SMS: latest500 messages in the current thread; reports: first500 matching records). Narrow search/date filters to inspect other records. TeslaFi daily charts show up to60 imported days at once. Exports retain all selected/matching records.
