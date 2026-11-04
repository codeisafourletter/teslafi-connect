# 1.0.0-rc.1

First functional candidate from an empty placeholder: a read-only, dependency-free logged-status client with an offline fixture mode. This provides a useful automation building block without introducing control permissions, paid infrastructure, or an account-management UI.

- Current and last-complete feed requests with environment-only token loading.
- Safe allowlisted JSON summary, explicit logged-data freshness limitation, token-safe errors, redirect rejection, response-size limit, request timeout, and no retries.
- Synthetic examples and Python 3.10/3.13 tests/CI.

No existing API or data migration. Run from the source checkout; no package has been published. The earlier placeholder remains the stable branch until this candidate is accepted.

## Acceptance before 1.0.0

CI must pass on both Python versions. An owner should verify one current-feed and one last-good request against their own account locally, checking expected field names and timestamp interpretation. **No live account has been tested for this candidate.** If a real response shape differs, add a redacted fixture before claiming support. Drive/charge history, charts, vehicle commands, and account configuration remain outside this candidate.
