from pathlib import Path
import json
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from pages import calendar_text
from refresh import collect


class PaymentTests(unittest.TestCase):
    def test_correction_replaces_year_and_keeps_history(self):
        config = {'x': {'name': 'Other benefit', 'anchor': 'x', 'region': 'CA', 'per_year': 1}}
        old = {'programs': {'x': {'dates': ['2025-01-12','2026-01-13']}}}
        html = '<details id="x-2026"><ul><li>January 14, 2026</li></ul></details>'
        d = collect(html, config, old, '2026-01-01')
        self.assertEqual(d['programs']['x']['dates'], ['2025-01-12','2026-01-14'])
        with self.assertRaises(ValueError):
            collect(html.replace('2026</li>', '2025</li>'), config, old, '2026-01-01')
        with self.assertRaises(ValueError):
            collect('<main>Sorry</main>', config, old, '2026-01-01')

    def test_publication_has_one_stable_uid_per_program_month(self):
        source = Path(__file__).resolve().parents[1] / 'web/data/calendar.json'
        data = json.loads(source.read_text())
        events = [(d,k,p) for k,p in data['programs'].items() for d in p['dates']]
        text = calendar_text(events, '20261126T010000Z')
        lines = text.split('\r\n')
        ids = [value for value in lines if value.startswith('UID:')]
        self.assertEqual(len(set(ids)), len(events))
        self.assertEqual(len(ids), data['record_count'])
        self.assertTrue(all(len(line.encode()) <= 75 for line in lines))
