import itertools
import unittest
from dataclasses import replace
from decimal import Decimal, localcontext

from dat_shadow import Bar, MAX_BARS, ShadowViolation, simulate, validate_bars


def bar(t, close='100'):
    return Bar(t, Decimal(close), Decimal(close) + 1, Decimal(close) - 1,
               Decimal(close), Decimal('50'))


class WorkstreamTests(unittest.TestCase):
    def run_sim(self, bars=None, **kwargs):
        return simulate([bar(1), bar(2, '110')] if bars is None else bars,
                        synthetic_id='SYNTH-A', observed_at=2, **kwargs)

    def test_exact_cost_aware_outcome(self):
        result = self.run_sim(quantity='2')
        self.assertEqual(Decimal(result.gross_pnl), Decimal('20'))
        self.assertEqual(Decimal(result.fees), Decimal('.42'))
        self.assertEqual(Decimal(result.slippage), Decimal('.84'))
        self.assertEqual(Decimal(result.net_pnl), Decimal('18.74'))
        self.assertEqual(result.mode, 'SHADOW')

    def test_repeatability_and_ambient_decimal_context(self):
        expected = self.run_sim()
        for _ in range(100):
            self.assertEqual(self.run_sim(), expected)
        with localcontext() as context:
            context.prec = 3
            self.assertEqual(self.run_sim(), expected)

    def test_costs_can_turn_gain_into_loss(self):
        result = self.run_sim([bar(1), bar(2, '100.1')])
        self.assertLess(Decimal(result.net_pnl), 0)

    def test_reject_live_modes_and_any_order_intent(self):
        for mode in ('LIVE', 'PAPER', '', None):
            with self.subTest(mode=mode), self.assertRaises(ShadowViolation):
                self.run_sim(mode=mode)
        for intent in ('BUY', {}, False, 0):
            with self.subTest(intent=intent), self.assertRaises(ShadowViolation):
                self.run_sim(order_intent=intent)

    def test_nonfinite_ohlcv_and_parameters(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            for field in ('open', 'high', 'low', 'close', 'volume'):
                with self.subTest(value=value, field=field), self.assertRaises(ShadowViolation):
                    self.run_sim([replace(bar(1), **{field: value}), bar(2)])
            for field in ('quantity', 'fee_bps', 'slippage_bps'):
                with self.subTest(value=value, field=field), self.assertRaises(ShadowViolation):
                    self.run_sim(**{field: value})

    def test_reject_future_duplicate_out_of_order(self):
        for bars in ([bar(1), bar(3)], [bar(2), bar(1)], [bar(1), bar(1)]):
            with self.subTest(bars=bars), self.assertRaises(ShadowViolation):
                self.run_sim(bars)

    def test_reject_invalid_geometry_and_time(self):
        for bad in (replace(bar(1), low='102'), replace(bar(1), high='98'),
                    replace(bar(1), close='0'), replace(bar(1), volume='-1'),
                    replace(bar(1), timestamp=True)):
            with self.subTest(bar=bad), self.assertRaises(ShadowViolation):
                self.run_sim([bad, bar(2)])
        for clock in (True, -1, '2'):
            with self.subTest(clock=clock), self.assertRaises(ShadowViolation):
                validate_bars([bar(1), bar(2)], observed_at=clock)

    def test_bounded_stream_and_boundary(self):
        count = 0
        def endless():
            nonlocal count
            for t in itertools.count():
                count += 1
                yield bar(t)
        with self.assertRaises(ShadowViolation):
            validate_bars(endless(), observed_at=1000000)
        self.assertEqual(count, MAX_BARS + 1)
        self.assertEqual(len(validate_bars((bar(t) for t in range(MAX_BARS)),
                                           observed_at=MAX_BARS)), MAX_BARS)

    def test_parameter_limits_and_synthetic_labels(self):
        for parameters in ({'quantity':'101'}, {'quantity':'0'}, {'fee_bps':'-1'},
                           {'slippage_bps':'10001'}, {'quantity':True}):
            with self.subTest(parameters=parameters), self.assertRaises(ShadowViolation):
                self.run_sim(**parameters)
        for label in ('EURUSD', 'SYNTH-', 'SYNTH-../../file', 'SYNTH-' + 'A' * 50):
            with self.subTest(label=label), self.assertRaises(ShadowViolation):
                simulate([bar(1),bar(2)], synthetic_id=label, observed_at=2)

    def test_numeric_resource_bounds(self):
        for value in ('1e999999999', '1e-999999999', '1' * 100):
            with self.subTest(value=value), self.assertRaises(ShadowViolation):
                self.run_sim(quantity=value)

    def test_minimum_sample_count(self):
        for bars in ([], [bar(1)]):
            with self.assertRaises(ShadowViolation):
                self.run_sim(bars)


if __name__ == '__main__':
    unittest.main()
