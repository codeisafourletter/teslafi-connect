import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from teslafi_connect.__main__ import FeedError, MAX_BYTES, decode_feed, main, summarize


class InspectorTests(unittest.TestCase):
    def test_real_input_path_preserves_logged_fields_and_omits_identity(self):
        record={'Date':'2025-01-02 12:00:00','state':'asleep','battery_level':'72','charging_state':'Disconnected','vin':'private-vin','latitude':1,'longitude':2}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'saved.json';path.write_text(json.dumps(record))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(['--input',str(path)]),0)
            result=json.loads(out.getvalue())
        self.assertEqual(result['recorded_at'],record['Date'])
        self.assertEqual(result['values']['battery_level'],'72')
        self.assertNotIn('private-vin',out.getvalue())
        self.assertNotIn('latitude',out.getvalue())
        self.assertIn('not inferred',result['freshness'])

    def test_bad_and_oversized_records_fail_without_echoing_payload(self):
        for payload in (b'private non-json',b'[]',b'{"error":"private"}',b'{"response":{"result":"unauthorized"}}',b'x'*(MAX_BYTES+1)):
            with self.assertRaises(FeedError) as result:decode_feed(payload)
            self.assertNotIn('private',str(result.exception))

    def test_unknown_status_does_not_succeed_silently(self):
        for data in ({},{'response':None},{'state':False},{'battery_level':True},{'battery_level':101},{'battery_level':float('nan')}):
            with self.subTest(data=data),self.assertRaises(FeedError):decode_feed(json.dumps(data).encode())
        self.assertEqual(decode_feed(b'{"battery_level":0}')['battery_level'],0)

    def test_missing_timestamp_is_unknown(self):
        self.assertIsNone(summarize({'state':'asleep'},'local')['recorded_at'])

    def test_missing_input_is_clear_nonzero(self):
        with contextlib.redirect_stderr(io.StringIO()) as out:
            self.assertEqual(main(['--input','missing-file.json']),1)
        self.assertEqual(out.getvalue().strip(),'Cannot read the local input file.')

    def test_synthetic_example_is_usable(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(['--input','examples/status.json']),0)
        self.assertEqual(json.loads(out.getvalue())['values']['state'],'asleep')


if __name__=='__main__':unittest.main()
