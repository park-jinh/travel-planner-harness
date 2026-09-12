import copy
import importlib.util
from pathlib import Path
import unittest
import json
import subprocess
import sys
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / 'harness/travel-planner/scripts/validate_plan.py'
spec = importlib.util.spec_from_file_location('validator', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    return dict(version=2, budget_currency='KRW', budget_amount=300000,
                required_ids=['a'], unresolved=[], costs=[dict(id='all', label='synthetic', currency='KRW', low_amount=100000, high_amount=200000)],
                items=[dict(id='first', candidate_id='a', kind='visit',
                            start='2026-10-01T10:00:00+09:00', end='2026-10-01T11:00:00+09:00',
                            windows=[['2026-10-01T09:00:00+09:00', '2026-10-01T12:00:00+09:00']],
                            incoming_minutes=0, evidence_status='verified')])


class ValidationTests(unittest.TestCase):
    def test_decimal_budget_exact(self):
        p = fixture(); p['budget_currency'] = 'USD'; p['budget_amount'] = 3.3
        p['costs'] = [dict(id=str(n), label='cost', currency='USD', low_amount=v, high_amount=v) for n,v in enumerate((1.1,2.2))]
        result = module.validate(p)
        self.assertFalse(result['errors'])
        self.assertEqual(result['cost_range'], [3.3,3.3])
        p['budget_amount'] = 3.29
        self.assertTrue(module.validate(p)['errors'])

    def test_invalid_collection_types(self):
        for field in ('items','costs','required_ids','unresolved'):
            for value in ('a',{},None,True):
                with self.subTest(field=field, value=value):
                    p = fixture(); p[field] = value
                    with self.assertRaises(ValueError): module.validate(p)

    def test_invalid_nested_records(self):
        for field in ('items','costs'):
            for value in (None,'a',[],{}):
                with self.subTest(field=field, value=value):
                    p = fixture(); p[field] = [value]
                    with self.assertRaises(ValueError): module.validate(p)

    def test_invalid_windows(self):
        for value in ({}, 'a', [[]], [['one']], [None]):
            p = fixture(); p['items'][0]['windows'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): module.validate(p)

    def test_invalid_ids(self):
        for value in ([], {}, 1, ''):
            p = fixture(); p['items'][0]['candidate_id'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): module.validate(p)

    def test_cli_rejects_malformed_input(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'plan.json'
            p = fixture(); p['costs'] = {}
            path.write_text(json.dumps(p), encoding='utf-8')
            result = subprocess.run([sys.executable,str(SCRIPT),str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('input_error',json.loads(result.stdout))

    def test_cli_decimal_budget(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'plan.json'
            p = fixture(); p['budget_amount'] = 3.3
            p['costs'] = [dict(id=str(n), label='cost', currency='KRW', low_amount=v, high_amount=v) for n,v in enumerate((1.1,2.2))]
            path.write_text(json.dumps(p),encoding='utf-8')
            result = subprocess.run([sys.executable,str(SCRIPT),str(path)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout)
            self.assertEqual(json.loads(result.stdout)['cost_range'],[3.3,3.3])

    def test_non_korean_currency(self):
        p = fixture(); p['budget_currency'] = 'EUR'; p['costs'][0]['currency'] = 'EUR'
        self.assertEqual(module.validate(p)['currency'], 'EUR')

    def test_mixed_currency_rejected(self):
        p = fixture(); p['costs'][0]['currency'] = 'USD'
        with self.assertRaises(ValueError): module.validate(p)

    def test_international_date_line(self):
        p = fixture(); p['required_ids'] = []
        p['items'][0].update(kind='transport', start='2026-10-02T17:00:00+09:00', end='2026-10-02T11:00:00-07:00', windows=None)
        self.assertFalse(module.validate(p)['errors'])

    def test_dst_fallback(self):
        p = fixture(); p['items'][0].update(start='2026-11-01T01:30:00-04:00', end='2026-11-01T01:15:00-05:00', windows=None)
        self.assertFalse(module.validate(p)['errors'])

    def test_cross_zone_overlap(self):
        p = fixture(); second = copy.deepcopy(p['items'][0])
        second.update(id='second', start='2026-10-01T01:30:00+00:00', end='2026-10-01T02:30:00+00:00', windows=None)
        p['items'].append(second)
        self.assertIn('overlap', str(module.validate(p)['errors']))

    def test_legacy_rejected_explicitly(self):
        p = fixture(); p['version'] = 1
        with self.assertRaisesRegex(ValueError, 'migrate'): module.validate(p)

    def test_valid(self):
        self.assertEqual(module.validate(fixture())['errors'], [])

    def test_closed(self):
        p = fixture(); p['items'][0]['windows'] = []
        self.assertIn('outside available windows', str(module.validate(p)['errors']))

    def test_break_time(self):
        p = fixture(); p['items'][0]['windows'][0][1] = '2026-10-01T10:30:00+09:00'
        self.assertTrue(module.validate(p)['errors'])

    def test_transfer_shortfall(self):
        p = fixture(); second = copy.deepcopy(p['items'][0])
        second.update(id='second', start='2026-10-01T11:10:00+09:00', end='2026-10-01T11:30:00+09:00', incoming_minutes=20)
        p['items'].append(second)
        self.assertIn('insufficient transfer', str(module.validate(p)['errors']))

    def test_overlap(self):
        p = fixture(); second = copy.deepcopy(p['items'][0]); second['id'] = 'second'
        p['items'].append(second)
        self.assertIn('overlap', str(module.validate(p)['errors']))

    def test_budget(self):
        p = fixture(); p['budget_amount'] = 150000
        self.assertTrue(module.validate(p)['errors'])

    def test_unknown_cost_not_free(self):
        p = fixture(); p['costs'][0].update(low_amount=None, high_amount=None)
        self.assertIn('unknown cost', str(module.validate(p)['warnings']))
        self.assertIsNone(module.validate(p)['cost_range'])

    def test_last_entry(self):
        p = fixture(); p['items'][0]['latest_entry'] = '2026-10-01T09:30:00+09:00'
        self.assertIn('latest entry', str(module.validate(p)['errors']))

    def test_transport_not_visit(self):
        p = fixture(); p['items'][0]['kind'] = 'transport'
        self.assertIn('required stop missing', str(module.validate(p)['errors']))

    def test_first_transfer(self):
        p = fixture(); p['items'][0]['incoming_minutes'] = 10
        self.assertTrue(module.validate(p)['errors'])

    def test_required_missing(self):
        p = fixture(); p['required_ids'].append('missing')
        self.assertTrue(module.validate(p)['errors'])

    def test_conflicting_evidence(self):
        p = fixture(); p['items'][0]['evidence_status'] = 'conflicting'
        self.assertIn('conflicting', str(module.validate(p)['warnings']))

    def test_timezone_required(self):
        p = fixture(); p['items'][0]['start'] = '2026-10-01T10:00:00'
        with self.assertRaises(ValueError): module.validate(p)

    def test_negative_cost(self):
        p = fixture(); p['costs'][0]['low_amount'] = -1
        with self.assertRaises(ValueError): module.validate(p)

    def test_overnight(self):
        p = fixture(); p['items'][0].update(start='2026-10-01T23:00:00+09:00', end='2026-10-02T01:00:00+09:00', windows=[['2026-10-01T22:00:00+09:00', '2026-10-02T02:00:00+09:00']])
        self.assertFalse(module.validate(p)['errors'])

    def test_empty(self):
        p = fixture(); p['items'] = []; p['required_ids'] = []
        self.assertTrue(module.validate(p)['errors'])


if __name__ == '__main__':
    unittest.main()
