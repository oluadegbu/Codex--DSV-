import copy
from decimal import Decimal, ROUND_FLOOR, localcontext
import unittest

from dpm_shadow import evaluate, InvalidResearchInput, MAX_PERIODS, MAX_SCENARIOS, MAX_ASSETS


def request():
    return {'version': 1, 'mode': 'SHADOW', 'intent': 'RESEARCH', 'scenarios': [
        {'name': 'two_assets', 'periods': [0, 1],
         'weights': {'A': '0.5', 'B': '0.5'},
         'returns': {'A': ['0.2', '-0.5'], 'B': ['0', '0']}}]}


class SyntheticResearchTests(unittest.TestCase):
    def test_fixed_initial_exposures_known_drawdown(self):
        result = evaluate(request())
        values = result['results'][0]
        self.assertEqual(Decimal(values['cumulative_return']), Decimal('-0.2'))
        self.assertAlmostEqual(float(values['max_drawdown']), 3 / 11)
        self.assertEqual(values['period_count'], 2)
        self.assertEqual(result['source'], 'synthetic_only')

    def test_repeat_and_ambient_precision_independence(self):
        expected = evaluate(request())
        with localcontext() as ctx:
            ctx.prec = 3
            ctx.rounding = ROUND_FLOOR
            self.assertEqual(evaluate(request()), expected)
        self.assertEqual(evaluate(request()), expected)

    def test_input_not_mutated(self):
        original = request()
        before = copy.deepcopy(original)
        evaluate(original)
        self.assertEqual(original, before)

    def test_total_loss_stays_zero(self):
        item = request()
        item['scenarios'][0]['weights'] = {'A': '1'}
        item['scenarios'][0]['returns'] = {'A': ['-1', '1']}
        values = evaluate(item)['results'][0]
        self.assertEqual(Decimal(values['cumulative_return']), -1)
        self.assertEqual(Decimal(values['max_drawdown']), 1)

    def test_reject_live_and_order_intent(self):
        for key, value in [('mode', 'LIVE'), ('intent', 'ORDER'), ('intent', 'REBALANCE')]:
            with self.subTest(key=key, value=value):
                item = request()
                item[key] = value
                with self.assertRaises(InvalidResearchInput):
                    evaluate(item)
        item = request()
        item['orders'] = []
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)

    def test_reject_nonfinite_and_unbounded_numeric(self):
        for value in ['NaN', 'Infinity', '-Infinity', '1e-999999', '2', '-1.1', True, 0.2, '9' * 65]:
            with self.subTest(value=value):
                item = request()
                item['scenarios'][0]['returns']['A'][0] = value
                with self.assertRaises(InvalidResearchInput):
                    evaluate(item)

    def test_reject_out_of_order_or_boolean_periods(self):
        for periods in [[1, 0], [0, 0], [0, 2], [False, 1], []]:
            with self.subTest(periods=periods):
                item = request()
                item['scenarios'][0]['periods'] = periods
                with self.assertRaises(InvalidResearchInput):
                    evaluate(item)

    def test_reject_malformed_series_and_weights(self):
        for weights, returns in [({'A': '1'}, {'B': ['0', '0']}),
                                 ({'A': '-1', 'B': '2'}, {'A': ['0', '0'], 'B': ['0', '0']}),
                                 ({'A': '0.9999999999999999999999999999999999999999'}, {'A': ['0', '0']}),
                                 ({'A': '1'}, {'A': ['0']}),
                                 ({1: '1'}, {1: ['0', '0']})]:
            with self.subTest(weights=weights):
                item = request()
                item['scenarios'][0].update(weights=weights, returns=returns)
                with self.assertRaises(InvalidResearchInput):
                    evaluate(item)

    def test_reject_version_unknown_fields_and_duplicates(self):
        for version in [True, 2]:
            item = request()
            item['version'] = version
            with self.assertRaises(InvalidResearchInput):
                evaluate(item)
        item = request()
        item['scenarios'].append(copy.deepcopy(item['scenarios'][0]))
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)
        item = request()
        item['scenarios'][0]['command'] = 'arbitrary'
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)

    def test_resource_limits(self):
        item = request()
        item['scenarios'] *= MAX_SCENARIOS + 1
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)
        item = request()
        item['scenarios'][0]['periods'] = list(range(MAX_PERIODS + 1))
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)
        item = request()
        item['scenarios'][0]['weights'] = {f'A{i}': '0' for i in range(MAX_ASSETS + 1)}
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)

    def test_total_sample_limit(self):
        item = request()
        item['scenarios'] = []
        for i in range(9):
            assets = {f'A{a}': '0.0625' for a in range(16)}
            item['scenarios'].append({'name': f'scenario_{i}', 'periods': list(range(512)),
                                      'weights': assets, 'returns': {a: ['0'] * 512 for a in assets}})
        with self.assertRaises(InvalidResearchInput):
            evaluate(item)

    def test_valid_max_periods_and_multiple_scenarios(self):
        item = request()
        item['scenarios'][0] = {'name': 'bounded', 'periods': list(range(MAX_PERIODS)),
                                'weights': {'A': '1'}, 'returns': {'A': ['0'] * MAX_PERIODS}}
        item['scenarios'].append({'name': 'growth', 'periods': [0],
                                  'weights': {'B': '1'}, 'returns': {'B': ['0.25']}})
        results = evaluate(item)['results']
        self.assertEqual([Decimal(r['cumulative_return']) for r in results], [0, Decimal('0.25')])
        self.assertTrue(all(Decimal(r['max_drawdown']) == 0 for r in results))


if __name__ == '__main__':
    unittest.main()
