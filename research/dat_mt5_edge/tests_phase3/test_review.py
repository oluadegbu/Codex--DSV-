import unittest
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from phase3.review import blockers,eligible,session,run,ROOT

class CertificationTests(unittest.TestCase):
    def test_all_existing_instruments_blocked(self):
        for s in ('EURUSD','GBPUSD','XAUUSD'):self.assertIn('PRIMARY_QUOTES_NOT_CROSSVERIFIED',blockers(s,{}))
    def test_gold_never_infers_scale(self):
        self.assertIn('PRICE_SCALE_UNRESOLVED',blockers('XAUUSD',{'median':13}))
    def test_no_certification_no_selection(self):
        self.assertFalse(eligible(False,1000,200,.2,.3,4))
    def test_sample_boundary(self):
        self.assertFalse(eligible(True,99,60,.1,.1,2))
        self.assertFalse(eligible(True,100,59,.1,.1,2))
    def test_no_positive_ci_or_stress(self):
        self.assertFalse(eligible(True,100,60,0,.1,2))
        self.assertFalse(eligible(True,100,60,.1,0,2))
    def test_fold_stability(self):
        self.assertFalse(eligible(True,100,60,.1,.1,1))
        self.assertTrue(eligible(True,100,60,.1,.1,2))
    def test_dst_mismatch_weeks(self):
        # NY already summer time while London still winter, and conversely autumn.
        for date in ('2025-03-17T06:30:00','2025-10-27T06:30:00'):
            self.assertEqual(session(datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp()),'02-05')
    def test_winter_session(self):
        self.assertEqual(session(datetime(2025,1,6,7,30,tzinfo=timezone.utc).timestamp()),'02-05')
    def test_drift_rejected_before_data_access(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'phase2/results';p.mkdir(parents=True);(p/'phase2.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'drift'):run(Path(d))
    def test_no_execution_dependency(self):
        import ast
        tree=ast.parse((ROOT/'phase3/review.py').read_text())
        modules=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):modules.extend(x.name for x in n.names)
            elif isinstance(n,ast.ImportFrom):modules.append(n.module)
        self.assertFalse(any(m.split('.')[0] in ('MetaTrader5','socket','requests','subprocess','boto3') for m in modules))

if __name__=='__main__':unittest.main()
