import contextlib
import io
import json
import unittest
from unittest.mock import patch
import urllib.error
from teslafi_connect.__main__ import FeedError, MAX_BYTES, NoRedirect, decode_feed, fetch_feed, main, summarize


class Response(io.BytesIO):
    pass


class Opener:
    def __init__(self, payload=b'{"state":"asleep"}', error=None):
        self.payload, self.error = payload, error
        self.request = None

    def open(self, request, timeout):
        self.request, self.timeout = request, timeout
        if self.error:
            raise self.error
        return Response(self.payload)


class FeedTests(unittest.TestCase):
    def test_read_only_bearer_and_last_good(self):
        opener = Opener()
        self.assertEqual(fetch_feed('secret', True, opener)['state'], 'asleep')
        self.assertEqual(opener.request.full_url, 'https://www.teslafi.com/feed.php?command=lastGood')
        self.assertNotIn('secret', opener.request.full_url)
        self.assertEqual(opener.request.get_header('Authorization'), 'Bearer secret')
        self.assertEqual(opener.request.get_method(), 'GET')
        self.assertEqual(opener.timeout, 20)

    def test_current_feed_empty_command(self):
        opener = Opener()
        fetch_feed('secret', opener=opener)
        self.assertTrue(opener.request.full_url.endswith('?command='))

    def test_missing_token_and_header_injection_rejected(self):
        for token in (None, '', '  ', 'abc\r\ndef'):
            with self.assertRaises(FeedError):
                fetch_feed(token, opener=Opener())

    def test_transport_error_does_not_echo_token(self):
        for error in (urllib.error.URLError('token=secret'), TimeoutError('secret'),
                      urllib.error.HTTPError('https://example/?secret', 401, 'secret', {}, None)):
            with self.assertRaises(FeedError) as result:
                fetch_feed('secret', opener=Opener(error=error))
            self.assertNotIn('secret', str(result.exception))

    def test_redirect_is_never_followed_with_credentials(self):
        with self.assertRaises(FeedError):
            NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.example')

    def test_bad_error_and_large_records(self):
        for payload in (b'not json secret', b'[]', b'{"error":"secret"}',
                        b'{"response":{"result":"unauthorized"}}', b'x' * (MAX_BYTES + 1)):
            with self.assertRaises(FeedError) as result:
                decode_feed(payload)
            self.assertNotIn('secret', str(result.exception))

    def test_summary_omits_location_identity_and_nested_data(self):
        result = summarize({'vin': 'private', 'latitude': 20, 'state': {'secret': 1}, 'Date': '2025'}, 'test')
        self.assertNotIn('private', json.dumps(result))
        self.assertEqual(result['values'], {})
        self.assertEqual(result['recorded_at'], '2025')

    def test_fixture_does_not_need_network_or_token(self):
        with patch('teslafi_connect.__main__.fetch_feed', side_effect=AssertionError('network')), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['--fixture', 'examples/status.json']), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(result['values']['battery_level'], '72')
        self.assertNotIn('SYNTHETIC-NOT', out.getvalue())


if __name__ == '__main__':
    unittest.main()
