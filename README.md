# TeslaFi Connect

A small, read-only Python client for a **logged TeslaFi status summary**. It never sends vehicle controls, wakes a car, or downloads account history.

**Status: 1.0.0-rc.1.** First working candidate from the former placeholder. Python 3.10+; no third-party dependencies. This repository's client is independent of the similarly named ChatGPT skill and does not install or configure that skill.

## Try without credentials

From this repository's directory:

```bash
python -m teslafi_connect --fixture examples/status.json
```

The synthetic example prints the record date, battery level, charging state, and vehicle state. VIN, location and account names are excluded. Missing values remain absent. Values retain TeslaFi's types; no unit conversion is performed.

## Read your logged status

Get a feed token while signed in at <https://www.teslafi.com/api.php>. Set `TESLAFI_API_TOKEN` in your local environment without putting it in Git, chat, shell history, or command arguments. In Bash, a hidden prompt avoids typing the token into a command:

```bash
read -rsp 'TeslaFi API token: ' TESLAFI_API_TOKEN; echo
export TESLAFI_API_TOKEN
python -m teslafi_connect
python -m teslafi_connect --last-good
unset TESLAFI_API_TOKEN
```

The token is sent only in the HTTPS Authorization header to `https://www.teslafi.com/feed.php`. The current feed uses an empty `command`; `--last-good` uses `command=lastGood`. Redirects are rejected. Requests have a 20-second timeout, a 2 MiB response limit, and no automatic retries. Transport/API errors do not echo token-bearing headers, URLs, or raw responses. A valid token and TeslaFi account are required for live use; none are bundled.

**Logged does not mean live.** `--last-good` may return an old record. The source timestamp is shown without inventing a timezone or freshness guarantee. Missing timestamps remain null. Sleeping/unavailable and incompatible responses fail clearly instead of fabricating status. Only a JSON object feed with documented flat summary fields is supported in this candidate.

## Check

```bash
python -m unittest discover -s tests -v
```

Tests use synthetic fixtures and mocked transport only. No live account request has been made. See [RELEASE_NOTES.md](RELEASE_NOTES.md) for acceptance criteria. No open-source license is granted.

API contract reference: [TeslaFi API page](https://www.teslafi.com/api.php). User-specific supported access is authoritative there. This client deliberately has no command execution interface.
