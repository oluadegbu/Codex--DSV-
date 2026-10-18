import csv,gzip,hashlib,io,json,unittest
from unittest.mock import patch
from phase5.sample import normalize,COLUMNS
from phase5.review import run

class SampleTests(unittest.TestCase):
    def raw(self,changes=None):
        rows=[['kraken','XBT/USD','1780272000000000','1780272000100000','1','100.1','100','2'],['kraken','XBT/USD','1780272000000000','1780272000100000','2','100.2','100.1','3']]
        if changes:changes(rows)
        f=io.StringIO();w=csv.writer(f);w.writerow(COLUMNS);w.writerows(rows);return gzip.compress(f.getvalue().encode(),mtime=0)
    def normalize_fixture(self,raw):
        with patch('phase5.sample.RAW_SHA',hashlib.sha256(raw).hexdigest()):return normalize(raw)
    def test_arrival_order_preserved_and_equal_times_not_dropped(self):
        data,r=self.normalize_fixture(self.raw());self.assertEqual(r['raw_quote_rows'],2);self.assertEqual(r['repeated_receive_timestamps'],1)
        row=next(csv.DictReader(io.StringIO(data.decode())));self.assertEqual(row['bid_open'],'100');self.assertEqual(row['bid_close'],'100.1')
    def test_bad_arrival_not_sorted_away(self):
        raw=self.raw(lambda rows:rows[1].__setitem__(3,'1780272000099999'))
        with self.assertRaisesRegex(ValueError,'arrival'):self.normalize_fixture(raw)
    def test_price_and_identity_failure(self):
        for pos,value in ((0,'other'),(1,'BTC/USDT'),(5,'99.9'),(6,'NaN')):
            with self.subTest(pos=pos),self.assertRaises(ValueError):self.normalize_fixture(self.raw(lambda rows:rows[1].__setitem__(pos,value)))
    def test_exchange_backstep_counted_not_sorted(self):
        _,r=self.normalize_fixture(self.raw(lambda rows:rows[1].__setitem__(2,'1780271999999999')));self.assertEqual(r['exchange_timestamp_backsteps'],1)
    def test_diagnostic_zeros_never_certify_free_trading(self):
        _,r=self.normalize_fixture(self.raw());self.assertEqual(r['certification']['status'],'QUARANTINED');self.assertFalse(r['certification']['research_ready'])
    def test_hash_drift(self):
        with self.assertRaisesRegex(ValueError,'hash drift'):normalize(self.raw())
    def test_actual_sample_and_frozen_baselines(self):
        r=run();self.assertEqual(r['paired_minutes'],1440);self.assertEqual(r['certified_datasets'],[]);self.assertEqual(r['spending_usd'],0)
    def test_offline_review_repeat(self):self.assertEqual(run(),run())
