import ast,json
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
import tempfile,unittest
from edge.core import Bar,Spec,Signal,validate_bars,run
from edge.strategies import STRATEGIES,NewYorkORB,LondonSweep
from edge.shadow import FileShadowFeed
T=datetime(2018,1,2,tzinfo=timezone.utc)
SPEC=Spec('BTCUSD','test',1,.01,.01,100,.01,0,0,0,short_allowed=True)
def bar(i,o=100,h=101,l=99,c=100):return Bar(T+timedelta(minutes=30*i),o,h,l,c,1)
class Once:
    def __init__(self,side=1,stop=95):self.n=0;self.side=side;self.stop=stop
    def observe(self,b):
        self.n+=1
        return Signal(self.side,self.stop,'test','fixture') if self.n==1 else None
class EngineTests(unittest.TestCase):
    def test_next_open_not_signal_close(self):
        tr,_=run([bar(0),bar(1,102,103,101,102),bar(2,102,103,101,102)],Once(),SPEC)
        self.assertEqual(len(tr),1);self.assertEqual(tr[0].entry,102)
        self.assertEqual(tr[0].entry_time,bar(1).time.isoformat())
    def test_stop_before_target(self):
        tr,_=run([bar(0),bar(1,100,115,90,100)],Once(),SPEC)
        self.assertEqual(tr[0].reason,'STOP');self.assertEqual(tr[0].exit,95)
        self.assertAlmostEqual(tr[0].r,-1)
    def test_gap_stop_uses_worse_open(self):
        tr,_=run([bar(0),bar(1,90,92,89,91)],Once(stop=95),SPEC)
        self.assertEqual(tr,[])
        tr,_=run([bar(0),bar(1,100,101,99,100),bar(2,90,92,89,91)],Once(),SPEC)
        self.assertEqual(tr[0].exit,90);self.assertLess(tr[0].r,-1)
    def test_missing_bar_cancels_pending(self):
        tr,s=run([bar(0),bar(2)],Once(),SPEC)
        self.assertEqual(tr,[]);self.assertEqual(s['rejected']['gap_signal'],1)
    def test_costs_and_cash_accounting(self):
        spec=replace(SPEC,spread_bps=10,commission_bps=20,slippage_bps=5)
        tr,s=run([bar(0),bar(1,100,101,99,100)],Once(),spec)
        t=tr[0];self.assertGreater(t.costs,0);self.assertLess(t.pnl,0)
        self.assertAlmostEqual(s['ending_equity']-spec.initial_equity,t.pnl)
        self.assertLessEqual(t.quantity*100,spec.initial_equity)
        self.assertAlmostEqual(t.pnl,-t.costs)
    def test_stress_worsens_flat_price_trade(self):
        spec=replace(SPEC,spread_bps=10,commission_bps=20,slippage_bps=5)
        a,_=run([bar(0),bar(1)],Once(),spec);b,_=run([bar(0),bar(1)],Once(),spec,stress=2)
        self.assertLess(b[0].r,a[0].r)
    def test_short_denied_without_borrow(self):
        tr,s=run([bar(0),bar(1)],Once(-1,105),replace(SPEC,short_allowed=False))
        self.assertEqual(tr,[]);self.assertEqual(s['rejected']['short_not_executable'],1)
    def test_prefix_results_are_causal(self):
        bars=[bar(i,100,101,99,100) for i in range(200)]
        for cls in STRATEGIES:
            a=cls();expected=[a.observe(b) for b in bars]
            for n in [1,20,50,100,150]:
                s=cls();self.assertEqual([s.observe(b) for b in bars[:n]],expected[:n])
    def test_ohlc_and_timestamp_fail_closed(self):
        for bars in [[bar(0),bar(0)],[bar(0,h=98)],[bar(0,c=float('nan'))],[replace(bar(0),time=T.replace(tzinfo=None))]]:
            with self.assertRaises(ValueError):validate_bars(bars)
    def test_ny_orb_sequential_break_then_retest(self):
        for day,hour in [(datetime(2018,1,2,tzinfo=timezone.utc),14),(datetime(2018,7,2,tzinfo=timezone.utc),13)]:
            s=NewYorkORB();base=day.replace(hour=hour,minute=30)
            a=Bar(base,100,102,98,101,1);b=Bar(base+timedelta(minutes=30),101,105,100,104,1)
            c=Bar(base+timedelta(minutes=60),104,106,101,105,1)
            self.assertIsNone(s.observe(a));self.assertIsNone(s.observe(b))
            sig=s.observe(c);self.assertEqual(sig.side,1);self.assertEqual(sig.stop,98)
    def test_london_sweep_requires_later_displacement(self):
        s=LondonSweep()
        for i in range(14):self.assertIsNone(s.observe(bar(i,100,102,98,101)))
        self.assertIsNone(s.observe(bar(14,101,105,100,101)))
        sig=s.observe(bar(15,101,102,97,98));self.assertEqual(sig.side,-1);self.assertEqual(sig.stop,105)
    def test_c_sweep_then_shift_then_later_ema_retest(self):
        from edge.strategies import SweepMSSFVG
        s=SweepMSSFVG();start=T-timedelta(hours=9)
        for i in range(48):
            b=replace(bar(i,100,102,98,101),time=start+timedelta(minutes=30*i))
            self.assertIsNone(s.observe(b))
        def b(i,o,h,l,c):return Bar(start+timedelta(minutes=30*i),o,h,l,c,1)
        self.assertIsNone(s.observe(b(48,100,101,97,99)))
        self.assertIsNone(s.observe(b(49,99,107,99,106)))
        sig=s.observe(b(50,106,108,100,107))
        self.assertEqual(sig.side,1);self.assertEqual(sig.stop,97)
    def test_drawdown_includes_open_adverse_excursion(self):
        _,stats=run([bar(0),bar(1,100,101,96,100)],Once(),SPEC)
        self.assertGreaterEqual(stats['max_drawdown_fraction'],.0019)
    def test_sizing_risk_and_lot_step(self):
        tr,_=run([bar(0),bar(1,100,101,99,100)],Once(),SPEC)
        self.assertLessEqual(tr[0].quantity*5,SPEC.initial_equity*SPEC.risk_fraction)
        self.assertAlmostEqual(tr[0].quantity/SPEC.quantity_step,round(tr[0].quantity/SPEC.quantity_step))
    def test_promotion_rejects_empty_and_unverified_data(self):
        from edge.research import experiment
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bars.csv'
            p.write_text('timestamp,open,high,low,close,volume\n'+''.join(
                f'{bar(i).time.isoformat()},100,101,99,100,1\n' for i in range(100)))
            result=experiment(p,SPEC)
            for x in result['results']:
                self.assertEqual(x['decision'],'REJECT')
                self.assertIn('OOS_SAMPLE_LT_100',x['rejection_reasons'])
                self.assertIn('UNVERIFIED_EXECUTABLE_PRICES_AND_CONTRACT',x['rejection_reasons'])
    def test_actual_market_prefix_causality(self):
        from edge.core import CsvBars
        path=Path('data/BTCUSD_30m.csv')
        if not path.exists():self.skipTest('optional public data not acquired')
        bars=CsvBars(path).bars()[:2000]
        for cls in STRATEGIES:
            obj=cls();full=[obj.observe(b) for b in bars]
            for n in (300,700,1400):
                obj=cls();self.assertEqual([obj.observe(b) for b in bars[:n]],full[:n])
    def test_weekend_ny_open_is_not_a_cash_session(self):
        s=NewYorkORB();base=datetime(2018,1,7,14,30,tzinfo=timezone.utc)
        for i,values in enumerate([(100,102,98,101),(101,105,100,104),(104,106,101,105)]):
            self.assertIsNone(s.observe(Bar(base+timedelta(minutes=30*i),*values,1)))
    def test_invalid_specs(self):
        for spec in [replace(SPEC,tick_size=0),replace(SPEC,spread_bps=-1),replace(SPEC,unit_value=float('nan'))]:
            with self.assertRaises(ValueError):spec.validate()
    def test_no_broker_or_process_imports(self):
        forbidden={'MetaTrader5','subprocess','socket','ctypes','requests'}
        for p in Path('edge').glob('*.py'):
            tree=ast.parse(p.read_text())
            imports={n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom) and n.module}
            imports|={a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
            self.assertFalse(imports & forbidden,p.name)
class ShadowTests(unittest.TestCase):
    def test_freshness_replay_and_symbol_gate(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'quote.json';feed=FileShadowFeed(p)
            x=dict(schema='DAT_MARKET_DATA_ONLY_V1',sequence=1,timestamp=T.isoformat(),symbol='BTCUSD',broker_symbol='BTCUSD',bid=100,ask=101,contract_verified=True,source='fixture')
            p.write_text(json.dumps(x));self.assertEqual(feed.read(T)['sequence'],1)
            with self.assertRaises(ValueError):feed.read(T)
            x['sequence']=2;p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):feed.read(T+timedelta(seconds=61))
            x['broker_symbol']='BTCUSDz';p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):FileShadowFeed(p).read(T)
            x['broker_symbol']='BTCUSD';x['password']='not-permitted';p.write_text(json.dumps(x))
            with self.assertRaises(ValueError):FileShadowFeed(p).read(T)
if __name__=='__main__':unittest.main()
