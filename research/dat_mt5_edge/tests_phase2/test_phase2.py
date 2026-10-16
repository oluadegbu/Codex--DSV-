import unittest,struct,lzma,math,tempfile,gzip,csv,json
from pathlib import Path
from datetime import datetime,date,timezone,timedelta
from dataclasses import replace
from phase2.model import QuoteBar,quality,aggregate,context,SPECS,clocks
from phase2.strategies import Intent,Variant,signals,variants
from phase2.engine import simulate,metrics,block_ci
from phase2.acquire_quotes import decode
T=int(datetime(2018,1,3,8,tzinfo=timezone.utc).timestamp())
def b(i,mid=1.2):return QuoteBar(T+i*60,mid,mid+.0001,mid-.0001,mid,mid+.0001,mid+.0002,mid,mid+.0001,1)
S=dict(SPECS['EURUSD'])
class ModelTests(unittest.TestCase):
    def test_partial_context_is_not_published(self):
        bars=[b(i)for i in range(59)];self.assertEqual(context(bars,60),{})
        ctx=context(bars+[b(59)],60);self.assertEqual(list(ctx),[T+3600])
    def test_aggregation_excludes_gaps(self):
        self.assertEqual(aggregate([b(0),b(2)],3),[])
        self.assertEqual(len(aggregate([b(0),b(1),b(2)],3)),1)
    def test_decoder_open_close_low_high_scale(self):
        raw=lzma.compress(struct.pack('>IIIIIf',0,120000,120010,119990,120020,1.))
        r=decode(raw,date(2020,1,1),100000)[0]
        self.assertEqual(r[1:5],(1.2,1.2002,1.1999,1.2001))
    def test_data_fail_closed(self):
        for rows in [[b(0),b(0)],[replace(b(0),ao=1.1)],[replace(b(0),bl=float('nan'))]]:
            with self.assertRaises(ValueError):quality(rows)
    def test_dst(self):
        winter=replace(b(0),t=int(datetime(2018,1,3,14,30,tzinfo=timezone.utc).timestamp()))
        summer=replace(b(0),t=int(datetime(2018,7,3,13,30,tzinfo=timezone.utc).timestamp()))
        self.assertEqual(clocks(winter)[1].hour,9);self.assertEqual(clocks(summer)[1].hour,9)
    def test_directions_and_stop_ambiguity(self):
        for side,stop in [(1,1.199),(-1,1.201)]:
            bars=[b(0),replace(b(1),bh=1.21,ah=1.2101,bl=1.19,al=1.1901)]
            tr,_=simulate(bars,[Intent(T+60,side,stop,'test')],S)
            self.assertEqual(tr[0].reason,'STOP');self.assertLess(tr[0].pnl,0)
            self.assertAlmostEqual(tr[0].r,-1.,places=8)
    def test_next_open_and_cost_stress(self):
        bars=[b(i)for i in range(3)];intent=Intent(T+60,1,1.199,'x')
        tr,_=simulate(bars,[intent],S);stress,_=simulate(bars,[intent],S,2)
        self.assertEqual(tr[0].entry,T+60);self.assertGreater(tr[0].entry_price,bars[1].bo)
        self.assertLess(stress[0].r,tr[0].r);self.assertGreater(tr[0].costs,0)
    def test_unknown_gap_cancels_signal(self):
        tr,_=simulate([b(0),b(2)],[Intent(T+120,1,1.199,'x')],S);self.assertEqual(tr,[])
    def test_no_overnight(self):
        t=int(datetime(2018,1,3,20,59,tzinfo=timezone.utc).timestamp())
        bars=[replace(b(i),t=t+i*60)for i in range(3)]
        tr,_=simulate(bars,[Intent(t+60,1,1.19,'x')],S)
        self.assertEqual(tr,[]) # entry outside 02–12 NY denied
    def test_prefix_causality_all_candidates(self):
        bars=[replace(b(i),bh=1.201,bl=1.199,ah=1.2011,al=1.1991)for i in range(240)]
        for v in variants('EURUSD'):
            full=signals(aggregate(bars,v.timeframe),v,bars)
            prefix=bars[:150]
            partial=signals(aggregate(prefix,v.timeframe),v,prefix)
            self.assertEqual(partial,[s for s in full if s.ready<=prefix[-1].end])
    def test_random_control_reproducible_and_varied(self):
        start=int(datetime(2018,1,3,0,tzinfo=timezone.utc).timestamp())
        bars=[replace(b(i),t=start+i*60)for i in range(1440)]
        v=Variant('random',5)
        one=signals(aggregate(bars,5),v,bars,seed=1)
        self.assertEqual(one,signals(aggregate(bars,5),v,bars,seed=1))
        two=signals(aggregate(bars,5),v,bars,seed=2)
        self.assertNotEqual(one,two)
    def test_late_entry_is_denied(self):
        tr,_=simulate([b(0),b(1)],[Intent(T+60,1,1.199,'x',T+60)],S)
        self.assertEqual(tr,[])
    def test_mae_mfe_and_fee_cash_accounting(self):
        bars=[b(i)for i in range(4)]
        tr,stats=simulate(bars,[Intent(T+60,1,1.199,'x')],S)
        self.assertAlmostEqual(stats['net_pnl'],sum(t.pnl for t in tr))
        self.assertGreaterEqual(tr[0].mae_r,0);self.assertGreaterEqual(tr[0].mfe_r,0)
    def test_gold_qualification_is_fail_closed(self):
        lock=json.loads(Path('phase2/source_lock.json').read_text())
        self.assertFalse(lock['data_qualification']['XAUUSD']['pilot_price_units_accepted'])
        self.assertFalse(SPECS['XAUUSD']['verified'])
    def test_futures_are_not_cfd_substitutions(self):
        from phase2.model import FUTURES
        self.assertEqual(set(FUTURES),{'ES','MES','NQ','MNQ','YM','MYM'})
        self.assertFalse(set(FUTURES)&set(SPECS))
    def test_actual_quote_prefix_causality(self):
        from phase2.model import load
        p=Path('phase2/work/data/EURUSD_1m.csv.gz')
        if not p.exists():self.skipTest('optional public dataset not present')
        bars,_=load(p);bars=bars[:5000]
        for v in [Variant('A',1),Variant('B',3),Variant('C',5)]:
            all_signals=signals(aggregate(bars,v.timeframe),v,bars)
            prefix=bars[:3000]
            self.assertEqual(signals(aggregate(prefix,v.timeframe),v,prefix),[x for x in all_signals if x.ready<=prefix[-1].end])
    def test_no_false_confidence_for_small_samples(self):
        self.assertIsNone(block_ci([]));self.assertIsNone(metrics([])['average_r'])
if __name__=='__main__':unittest.main()
