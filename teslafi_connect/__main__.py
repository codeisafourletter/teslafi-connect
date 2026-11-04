"""Read only the logged TeslaFi feed; never send a vehicle control."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

from . import __version__

ENDPOINT = 'https://www.teslafi.com/feed.php'
MAX_BYTES = 2 * 1024 * 1024


class FeedError(Exception):
    """Safe user-facing errors never include request URLs, headers or bodies."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedError('Unexpected redirect; verify TeslaFi service availability.')


def status_values(data):
    values = {}
    for key in ('state', 'charging_state'):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            values[key] = value
    battery = data.get('battery_level')
    if not isinstance(battery, bool):
        try:
            numeric = float(battery)
            if math.isfinite(numeric) and 0 <= numeric <= 100:
                values['battery_level'] = battery
        except (ValueError, TypeError, OverflowError):
            pass
    return values


def decode_feed(payload):
    if len(payload) > MAX_BYTES:
        raise FeedError('Feed exceeds the 2 MiB response limit.')
    try:
        data = json.loads(payload)
    except (ValueError, UnicodeError):
        raise FeedError('TeslaFi returned a non-JSON record; the vehicle may be asleep or unavailable. Try --last-good.') from None
    if not isinstance(data, dict):
        raise FeedError('Unsupported feed shape: expected a JSON object. No data was displayed.')
    if data.get('error') or data.get('error_description'):
        raise FeedError('TeslaFi reported an API error. Check token access on the TeslaFi API page.')
    response = data.get('response')
    if isinstance(response, dict) and (response.get('result') is False or response.get('result') == 'unauthorized'):
        raise FeedError('TeslaFi denied this request. Check token access on the TeslaFi API page.')
    valid_values = status_values(data)
    if not valid_values:
        raise FeedError('No recognized status fields in the feed. The record may be unavailable or incompatible; try --last-good.')
    return data


def fetch_feed(token, last_good=False, opener=None):
    if not token or not token.strip():
        raise FeedError('Set TESLAFI_API_TOKEN locally before requesting the feed; do not paste it into chat.')
    if not token.isascii() or any(ord(char) < 32 or ord(char) == 127 for char in token):
        raise FeedError('TESLAFI_API_TOKEN must contain printable ASCII characters only.')
    request = urllib.request.Request(
        ENDPOINT + ('?command=lastGood' if last_good else '?command='),
        headers={'Authorization': 'Bearer ' + token.strip(), 'Accept': 'application/json',
                 'User-Agent': 'teslafi-connect/' + __version__},
        method='GET',
    )
    opener = opener or urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(request, timeout=20) as response:
            return decode_feed(response.read(MAX_BYTES + 1))
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            raise FeedError('TeslaFi denied access. Verify your API token and feed permissions.') from None
        raise FeedError(f'TeslaFi returned HTTP {error.code}. No automatic retry was made.') from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise FeedError('TeslaFi could not be reached within the request timeout. No automatic retry was made.') from None


def summarize(data, source):
    # A deliberately small allowlist avoids VIN, location, account names and raw responses.
    values = status_values(data)
    recorded_at = data.get('Date', data.get('date'))
    if not isinstance(recorded_at, (str, int, float, type(None))):
        recorded_at = None
    return {'version': __version__, 'source': source, 'recorded_at': recorded_at,
            'freshness': 'Logged record only; timestamp timezone and age are not inferred.',
            'values': values}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read a logged TeslaFi status summary. No vehicle controls or wake requests.')
    parser.add_argument('--fixture', type=Path, help='Read a local JSON record without network or credentials')
    parser.add_argument('--last-good', action='store_true', help='Request the last complete logged record')
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args(argv)
    try:
        if args.fixture:
            with args.fixture.open('rb') as handle:
                data = decode_feed(handle.read(MAX_BYTES + 1))
            source = 'local fixture'
        else:
            data = fetch_feed(os.environ.get('TESLAFI_API_TOKEN'), args.last_good)
            source = 'last complete logged record' if args.last_good else 'current feed record'
        print(json.dumps(summarize(data, source), indent=2))
    except FeedError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print('Cannot read the local fixture file.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
