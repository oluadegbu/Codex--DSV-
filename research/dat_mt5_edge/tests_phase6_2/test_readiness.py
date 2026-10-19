"""Synthetic software fixtures only: NEVER profitability evidence."""
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from phase6_2.readiness import (Fold,normalize_timestamp,validate_folds,validate_sealed_holdout,
    research_gate, Contract, Quote, hypothetical_round_trip,sensitivity_grid, robustness_screen,
    SEALED_2026_HOLDOUT_START)
from phase6_2.shadow import ShadowJournal


class FoldTests(unittest.TestCase):
    def test_fixed_est_not_new_york_dst(self):
        self.assertEqual(normalize_timestamp('2026-07-01T10:00:00','EST_NO_DST'),
                         normalize_timestamp('2026-07-01T15:00:00+00:00','UTC'))
    def test_missing_timezone_denied(self):
        with self.assertRaises(ValueError):normalize_timestamp('2026-07-01T10:00:00','UTC')
    def test_ambiguous_source_timezone_denied(self):
        with self.assertRaises(ValueError):normalize_timestamp('2026-07-01T10:00:00','America/New_York')
    def test_chronological_embargo(self):
        f=[Fold('f1',100,200,210,250),Fold('f2',100,260,270,310)]
        self.assertEqual(len(validate_folds(f,10)),2)
    def test_overlap_denied(self):
        with self.assertRaises(ValueError):validate_folds([Fold('a',1,2,3,10),Fold('b',1,4,5,12)],0)
    def test_embargo_denied(self):
        with self.assertRaises(ValueError):validate_folds([Fold('a',100,200,205,300)],10)
    def test_duplicate_names_denied(self):
        with self.assertRaises(ValueError):validate_folds([Fold('a',1,2,3,4),Fold('a',1,4,5,6)],0)
    def test_sealed_holdout_denied(self):
        f=Fold('holdout',SEALED_2026_HOLDOUT_START-200,SEALED_2026_HOLDOUT_START-100,
               SEALED_2026_HOLDOUT_START,SEALED_2026_HOLDOUT_START+100)
        with self.assertRaises(ValueError):validate_sealed_holdout([f],SEALED_2026_HOLDOUT_START)
    def test_default_empty_sample_fail_closed(self):
        f=[Fold('a',0,10,60,360)]
        g=research_gate(folds=f,expected_by_fold={'a':{60,120,180}},observed_by_fold={'a':{60,120}},
            trades_by_fold={'a':[]})
        self.assertFalse(g['research_eligible']);self.assertFalse(g['edge_certified'])
        self.assertIn('CERTIFIED_DATA_EVIDENCE_REQUIRED',g['failures'])
        self.assertIn('MIN_COVERAGE_FOLD:a',g['failures'])
    def test_synthetic_sample_gate_only(self):
        # Example inputs deliberately unrealistic; software eligibility != edge certification.
        f=[Fold('f',0,1,10,86400*12)]
        timestamps={86400*d+100 for d in range(11)}
        rows=[{'timestamp':t,'session':('ASIA','LONDON','NEW_YORK')[i%3],
               'regime':('TREND','RANGE','VOLATILE')[i%3]} for i,t in enumerate(sorted(timestamps))]
        r=research_gate(folds=f,expected_by_fold={'f':timestamps},observed_by_fold={'f':timestamps},
           trades_by_fold={'f':rows},min_trades=10,min_fold_trades=10,min_active_days=10,
           min_segment_trades=3,evidence_certified=True)
        self.assertTrue(r['research_eligible']);self.assertFalse(r['edge_certified'])
        self.assertFalse(r['execution_authority'])
    def test_unreviewed_observation_denied(self):
        f=[Fold('f',0,10,60,180)]
        with self.assertRaises(ValueError):research_gate(folds=f,expected_by_fold={'f':{60}},
             observed_by_fold={'f':{60,120}},trades_by_fold={'f':[]})
    def test_mismatched_fold_denied(self):
        f=[Fold('f',0,10,60,180)]
        with self.assertRaises(ValueError):research_gate(folds=f,expected_by_fold={'other':{60}},
             observed_by_fold={'f':{60}},trades_by_fold={'f':[]})
    def test_missing_session_and_regime_gates(self):
        f=[Fold('f',0,10,60,180)]
        r=research_gate(folds=f,expected_by_fold={'f':{60}},observed_by_fold={'f':{60}},
          trades_by_fold={'f':[{'timestamp':60,'session':'ASIA','regime':'RANGE'}]},
          min_active_days=1,min_trades=1,min_fold_trades=1,min_segment_trades=1,evidence_certified=True)
        self.assertIn('MIN_SESSION:LONDON',r['failures']);self.assertIn('MIN_REGIME:TREND',r['failures'])


class RobustnessTests(unittest.TestCase):
    def test_empty_scenario_matrix_fails(self):
        a=robustness_screen([])
        self.assertFalse(a['exploratory_screen_pass']);self.assertFalse(a['edge_certified'])
    def test_incomplete_scenarios_denied(self):
        with self.assertRaises(ValueError):robustness_screen([
            dict(trade_id='one',session='ASIA',regime='TREND',scenario='baseline_1tick',net_r='1')])
    def test_complete_synthetic_matrix_still_not_edge(self):
        scenarios=('baseline_1tick','spread_2x','slippage_2ticks','commission_2x','financing_2x','combined_stress')
        rows=[dict(trade_id=f's{i}',session=('ASIA','LONDON','NEW_YORK')[i%3],
                   regime=('TREND','RANGE','VOLATILE')[i%3],scenario=scenario,net_r='0.1')
              for i in range(12) for scenario in scenarios]
        a=robustness_screen(rows,min_segment_trades=4)
        self.assertTrue(a['exploratory_screen_pass']);self.assertFalse(a['edge_certified'])
    def test_stress_negative_segment_blocks(self):
        scenarios=('baseline_1tick','spread_2x','slippage_2ticks','commission_2x','financing_2x','combined_stress')
        rows=[dict(trade_id=f's{i}',session='ASIA',regime='TREND',scenario=scenario,
                   net_r='-0.1' if scenario=='combined_stress' else '0.1')
              for i in range(5) for scenario in scenarios]
        a=robustness_screen(rows,min_segment_trades=2,sessions=('ASIA',),regimes=('TREND',))
        self.assertFalse(a['exploratory_screen_pass'])
        self.assertTrue(any('combined_stress' in f for f in a['failures']))


class FillTests(unittest.TestCase):
    def setUp(self):
        self.c=Contract('EURUSD','USD',Decimal('0.0001'),Decimal('1'),Decimal('2'),Decimal('3'),True)
        self.a=Quote(1000,Decimal('1.1000'),Decimal('1.1002'))
        self.b=Quote(2000,Decimal('1.1010'),Decimal('1.1012'))
    def test_long_uses_ask_then_bid(self):
        o=hypothetical_round_trip(self.a,self.b,side=1,quantity='1',contract=self.c)
        self.assertEqual(o['entry_price'],'1.1002');self.assertEqual(o['exit_price'],'1.1010')
        self.assertEqual(Decimal(o['net_pnl']),Decimal('4')) # 8 ticks less 4 commission
    def test_short_uses_bid_then_ask(self):
        o=hypothetical_round_trip(self.a,self.b,side=-1,quantity='1',contract=self.c)
        self.assertEqual(o['entry_price'],'1.1000');self.assertEqual(o['exit_price'],'1.1012')
        self.assertEqual(Decimal(o['net_pnl']),Decimal('-16'))
    def test_financing_charge(self):
        o=hypothetical_round_trip(self.a,self.b,side=1,quantity='1',contract=self.c,financing_nights=2)
        self.assertEqual(Decimal(o['financing']),Decimal('6'))
    def test_cost_stress_never_improves_long(self):
        rows=sensitivity_grid(self.a,self.b,side=1,quantity='1',contract=self.c,financing_nights=2)
        self.assertEqual(len(rows),6)
        self.assertTrue(all(Decimal(x['net_pnl']) <= Decimal(rows[0]['net_pnl']) for x in rows))
    def test_unverified_contract_denied(self):
        c=Contract('EURUSD','USD',Decimal('.0001'),Decimal('1'),Decimal('2'),Decimal('0'),False)
        with self.assertRaises(ValueError):hypothetical_round_trip(self.a,self.b,side=1,quantity='1',contract=c)
    def test_crossed_quote_denied(self):
        with self.assertRaises(ValueError):hypothetical_round_trip(self.a,Quote(2000,Decimal('1.1003'),Decimal('1.1002')),
                              side=1,quantity='1',contract=self.c)
    def test_invalid_scenario_denied(self):
        with self.assertRaises(ValueError):hypothetical_round_trip(self.a,self.b,side=1,quantity='1',contract=self.c,
                                                     spread_mult='0')
    def test_chronology_denied(self):
        with self.assertRaises(ValueError):hypothetical_round_trip(self.b,self.a,side=1,quantity='1',contract=self.c)


def payload(sequence, timestamp, bid='1.1000', ask='1.1002', source='offline'):
    return json.dumps({'schema':'MT5_QUOTES_V1','source_id':source,'symbol':'EURUSD',
       'sequence':sequence,'timestamp_ms':timestamp,'bid':bid,'ask':ask}).encode()

class ShadowTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.path=Path(self.dir.name)/'shadow.sqlite3'
        self.opts=dict(source_id='offline',symbol='EURUSD',tick_size='0.0001',max_spread='0.0005')
    def tearDown(self):self.dir.cleanup()
    def test_missing_journal_denied(self):
        with self.assertRaises(ValueError):ShadowJournal(self.path,**self.opts)
    def test_accept_and_restart_duplicate_denied(self):
        j=ShadowJournal(self.path,initialize=True,**self.opts)
        self.assertEqual(j.accept(payload(1,1000),1100)[-1],1);j.close()
        j=ShadowJournal(self.path,**self.opts)
        with self.assertRaises(ValueError):j.accept(payload(1,1000),1100)
        self.assertEqual(j.accept(payload(2,1100),1200)[-1],2);j.close()
    def test_rejection_does_not_advance(self):
        j=ShadowJournal(self.path,initialize=True,**self.opts)
        with self.assertRaises(ValueError):j.accept(payload(1,1000),8000) # stale
        self.assertEqual(j.accept(payload(1,1000),1100)[-1],1);j.close()
    def test_duplicate_json_key_denied(self):
        j=ShadowJournal(self.path,initialize=True,**self.opts)
        x=payload(1,1000).replace(b'"bid": ',b'"bid": "2", "bid": ',1)
        with self.assertRaises(ValueError):j.accept(x,1100)
        j.close()
    def test_mismatched_source_denied(self):
        j=ShadowJournal(self.path,initialize=True,**self.opts);j.close()
        with self.assertRaises(ValueError):ShadowJournal(self.path,source_id='other',symbol='EURUSD',tick_size='.0001',max_spread='.0005')
    def test_out_of_order_and_future_denied(self):
        j=ShadowJournal(self.path,initialize=True,**self.opts)
        j.accept(payload(1,1000),1100)
        with self.assertRaises(ValueError):j.accept(payload(2,900),1100)
        with self.assertRaises(ValueError):j.accept(payload(2,3000),1100)
        j.close()
    def test_missing_identity_record_denied(self):
        import sqlite3
        j=ShadowJournal(self.path,initialize=True,**self.opts);j.close()
        db=sqlite3.connect(self.path);db.execute('DELETE FROM identity');db.commit();db.close()
        with self.assertRaises(ValueError):ShadowJournal(self.path,initialize=True,**self.opts)


if __name__=='__main__':unittest.main()
