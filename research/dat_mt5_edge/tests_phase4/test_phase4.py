import ast,copy,csv,io,json,unittest
from pathlib import Path
from phase4.certify import canonical,certify,sha,validate_quotes,utc_epoch,FIELDS,PROOFS
from phase4.collector import PassiveCollector

BASE=1767225600

def fixture():
    out=io.StringIO();w=csv.writer(out,lineterminator='\n');w.writerow(FIELDS)
    for t in (BASE,BASE+60):w.writerow([t,'1.10000','1.10002','1.09999','1.10001','1.10002','1.10004','1.10001','1.10003','0'])
    raw=out.getvalue().encode();cal=canonical([BASE,BASE+60]);proofs={r:('Synthetic test proof '+r).encode() for r in PROOFS}
    m={'data_sha256':sha(raw),'calendar_sha256':sha(cal),'proofs':{r:sha(b) for r,b in proofs.items()},
       'contract':{'symbol':'EURUSD','venue':'SYNTHETIC_TEST_ONLY','price_units':'USD/EUR','pnl_currency':'USD',
                   'volume_semantics':'available_quote_volume','tick_size':'0.00001','digits':5,'point_value':'1','tick_value':'0.00001'},
       'costs':{'commission_per_side':'1','slippage_ticks':'1','financing_per_day':'0','currency':'USD','schedule_date':'2026-01-01'},
       'timezone':'UTC','timestamp_semantics':'BAR_OPEN','previously_evaluated_intervals':[]}
    return m,raw,cal,proofs

class CertifyTests(unittest.TestCase):
    def check_fixture(self,change=None,rawchange=None,calchange=None,trust=True):
        m,raw,cal,proofs=fixture()
        if change:change(m)
        if rawchange:raw=rawchange(raw)
        if calchange:cal=calchange(cal)
        return certify(m,raw,cal,proofs,[sha(canonical(m))] if trust else [],BASE+86400)
    def test_synthetic_positive_path_not_research_ready(self):
        r=self.check_fixture();self.assertEqual(r['status'],'CERTIFIED_RESEARCH_DATA');self.assertFalse(r['research_ready'])
    def test_cannot_self_certify(self):
        r=self.check_fixture(lambda m:m.update(verified=True),trust=False);self.assertIn('UNREVIEWED_EVIDENCE_BUNDLE',r['blockers'])
    def test_raw_hash_tamper(self):
        self.assertIn('DATA_HASH_MISMATCH',self.check_fixture(rawchange=lambda b:b+b'\n')['blockers'])
    def test_missing_proof(self):
        r=self.check_fixture(lambda m:m['proofs'].pop('license'));self.assertIn('MISSING_OR_CHANGED_LICENSE',r['blockers'])
    def test_calendar_cannot_be_inferred_from_data(self):
        r=self.check_fixture(calchange=lambda b:canonical([BASE,BASE+60,BASE+120]));self.assertEqual(r['coverage']['missing'],1);self.assertFalse(r['research_ready'])
    def test_outside_calendar(self):
        self.assertEqual(self.check_fixture(calchange=lambda b:canonical([BASE]))['coverage']['outside'],1)
    def test_duplicate_calendar(self):
        self.assertIn('INVALID_CALENDAR',self.check_fixture(calchange=lambda b:canonical([BASE,BASE]))['blockers'])
    def test_prior_holdout_never_fresh(self):
        r=self.check_fixture(lambda m:m.update(previously_evaluated_intervals=[[BASE,BASE+120]]));self.assertFalse(r['fresh_oos']);self.assertIn('PREVIOUSLY_EVALUATED_NOT_FRESH_OOS',r['blockers'])
    def test_missing_holdout_lineage(self):
        self.assertIn('MISSING_HOLDOUT_LINEAGE',self.check_fixture(lambda m:m.pop('previously_evaluated_intervals'))['blockers'])
    def test_inconsistent_tick_value(self):
        r=self.check_fixture(lambda m:m['contract'].update(tick_value='1'));self.assertTrue(any('tick-value' in b for b in r['blockers']))
    def test_gold_no_auto_scaling(self):
        r=self.check_fixture(lambda m:m['contract'].update(tick_size='0.01',digits=2));self.assertEqual(r['status'],'QUARANTINED')
    def test_broker_mapping_required_for_shadow(self):
        r=self.check_fixture(lambda m:m.update(purpose='broker_shadow'));self.assertEqual(r['status'],'QUARANTINED')
    def test_adjusted_futures_denied(self):
        r=self.check_fixture(lambda m:m.update(asset_class='futures',adjusted_prices=True));self.assertEqual(r['status'],'QUARANTINED')
    def test_zero_volume_not_imputed(self):
        self.assertEqual(self.check_fixture()['quality']['zero_volume'],2)
    def test_fixed_est_not_ny_dst(self):
        self.assertEqual(utc_epoch('2025-07-01T00:00:00','EST_NO_DST')-utc_epoch('2025-07-01T00:00:00','UTC'),18000)
        with self.assertRaises(ValueError):utc_epoch('2025-11-02T01:30:00','America/New_York')
    def test_structure_failures(self):
        _,raw,_,_=fixture();lines=raw.splitlines()
        for broken in [b'\n'.join([lines[0],lines[1],lines[1]])+b'\n',raw.replace(b'1.10000',b'NaN',1),raw.replace(b'1.10002',b'1.100025',1),b'\n'.join([lines[0],lines[2],lines[1]])+b'\n']:
            with self.subTest(broken=broken[:50]):
                with self.assertRaises(ValueError):validate_quotes(broken,'0.00001',5)
    def test_deterministic(self):self.assertEqual(self.check_fixture(),self.check_fixture())

class CollectorTests(unittest.TestCase):
    def packet(self,**changes):
        d=dict(schema='MT5_QUOTES_V1',source_id='TEST_ONLY',symbol='EURUSD',sequence=1,timestamp_ms=10000,bid='1.10000',ask='1.10002');d.update(changes);return json.dumps(d).encode()
    def collector(self):return PassiveCollector('TEST_ONLY','EURUSD','0.00001','0.001')
    def test_quote_only(self):self.assertEqual(self.collector().consume(self.packet(),10000)[0],'EURUSD')
    def test_order_fields_rejected(self):
        for k in ('order_send','order_modify','action','account','password','login','volume','callback','__class__'):
            with self.subTest(key=k),self.assertRaises(ValueError):self.collector().consume(self.packet(**{k:'x'}),10000)
    def test_invalid_packet_does_not_advance(self):
        c=self.collector()
        with self.assertRaises(ValueError):c.consume(self.packet(ask='1.00000'),10000)
        self.assertEqual(c.consume(self.packet(),10000)[-1],1)
    def test_replays(self):
        c=self.collector();c.consume(self.packet(),10000)
        with self.assertRaises(ValueError):c.consume(self.packet(sequence=2),10000)
        with self.assertRaises(ValueError):c.consume(self.packet(timestamp_ms=10001),10001)
    def test_bad_identity_clock_type_and_price(self):
        for change in ({'symbol':'XAUUSD'},{'source_id':'other'},{'sequence':True},{'timestamp_ms':True},{'bid':'NaN'},{'ask':'1.2'},{'bid':'1.100001'},{'bid':1.1},{'timestamp_ms':10001},{'timestamp_ms':1}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.collector().consume(self.packet(**change),10000)
    def test_duplicate_json_and_bounded_input(self):
        with self.assertRaises(ValueError):self.collector().consume(self.packet()[:-1]+b',"bid":"1.1"}',10000)
        with self.assertRaises(ValueError):self.collector().consume(b' '*4097,10000)
    def test_collector_capability_boundary(self):
        path=Path(__file__).resolve().parents[1]/'phase4/collector.py';tree=ast.parse(path.read_text());imports=[]
        forbidden={'open','exec','eval','compile','__import__','getattr','setattr','delattr','globals','locals','vars','input','breakpoint'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):imports.extend(x.name for x in n.names)
            if isinstance(n,ast.ImportFrom):imports.append(n.module)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,forbidden)
            if isinstance(n,ast.Attribute):self.assertFalse(n.attr.startswith('__'))
        self.assertEqual(set(imports),{'json','decimal'})
        self.assertEqual({n for n in vars(PassiveCollector) if not n.startswith('__')},{'consume'})

if __name__=='__main__':unittest.main()

class RuntimeAndBaselineTests(unittest.TestCase):
    def test_consumer_works_when_external_io_disabled(self):
        from unittest.mock import patch
        from phase4.collector import PassiveCollector
        packet=CollectorTests().packet()
        def deny(*args,**kwargs):raise AssertionError('external capability invoked')
        c=PassiveCollector('TEST_ONLY','EURUSD','0.00001','0.001')
        with patch('builtins.open',deny),patch('builtins.__import__',deny):
            self.assertEqual(c.consume(packet,10000)[-1],1)
    def test_capability_audit_pinned_source(self):
        from phase4.capability_audit import audit
        r=audit(Path(__file__).resolve().parents[1]/'phase4/collector.py');self.assertTrue(r['pass'],r)
    def test_baseline_and_repeat_results(self):
        from phase4.run import run,ROOT
        files=[ROOT/'phase4/results/readiness.json',ROOT/'phase4/results/recovery.json']
        run();a=[sha(p.read_bytes()) for p in files];run();self.assertEqual(a,[sha(p.read_bytes()) for p in files])
        result=json.loads(files[0].read_bytes());self.assertTrue(result['baseline_unchanged']);self.assertEqual(result['certified_instruments'],[])
        self.assertEqual(result['new_edge_backtests'],0)

class PackageBoundaryTests(unittest.TestCase):
    def test_package_path_and_size_limits(self):
        from tempfile import TemporaryDirectory
        from phase4.certify_package import bounded
        with TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_bytes(b'123');(p/'link').symlink_to(p/'a')
            for name,limit in [('../a',9),('link',9),('a',2),('/etc/passwd',9999)]:
                with self.subTest(name=name),self.assertRaises(ValueError):bounded(p,name,limit)
            self.assertEqual(bounded(p,'a',3),b'123')
    def test_package_cannot_supply_own_trust(self):
        from tempfile import TemporaryDirectory
        from phase4.certify_package import run
        m,raw,cal,proofs=fixture()
        with TemporaryDirectory() as d:
            p=Path(d);(p/'proofs').mkdir();(p/'manifest.json').write_bytes(canonical(m));(p/'quotes.csv').write_bytes(raw);(p/'calendar.json').write_bytes(cal)
            for role,data in proofs.items():(p/'proofs'/f'{role}.txt').write_bytes(data)
            (p/'reviewed_bundles.json').write_text(json.dumps({'bundle_sha256':[sha(canonical(m))]}))
            self.assertIn('UNREVIEWED_EVIDENCE_BUNDLE',run(p,BASE+86400)['blockers'])
