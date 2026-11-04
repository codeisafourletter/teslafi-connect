"""Inspect a local logged TeslaFi feed record without contacting any service."""
import argparse
import json
import math
from pathlib import Path
import sys

from . import __version__

MAX_BYTES = 2 * 1024 * 1024


class FeedError(Exception):
    """Safe user-facing errors never include request URLs, headers or bodies."""


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
        raise FeedError('Input is not a JSON record. Export a saved JSON feed record, not an HTML or text response.') from None
    if not isinstance(data, dict):
        raise FeedError('Unsupported feed shape: expected a JSON object. No data was displayed.')
    if data.get('error') or data.get('error_description'):
        raise FeedError('Input contains a TeslaFi API error, not a usable status record.')
    response = data.get('response')
    if isinstance(response, dict) and (response.get('result') is False or response.get('result') == 'unauthorized'):
        raise FeedError('Input contains a denied/unsuccessful API response, not a usable status record.')
    valid_values = status_values(data)
    if not valid_values:
        raise FeedError('No recognized status fields in the feed. The saved record may be unavailable or incompatible.')
    return data


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
    parser = argparse.ArgumentParser(description='Inspect a local TeslaFi JSON feed record. No network or account access.')
    parser.add_argument('--input', required=True, type=Path, help='Path to a saved JSON feed record')
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args(argv)
    try:
        with args.input.open('rb') as handle:
            data = decode_feed(handle.read(MAX_BYTES + 1))
        print(json.dumps(summarize(data, 'local saved record'), indent=2))
    except FeedError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print('Cannot read the local input file.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
